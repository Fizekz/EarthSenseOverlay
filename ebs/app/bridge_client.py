"""
Websocket client for the robot's TSP controller.

Read this before touching dispatch logic.

TEMPORARY DIRECT-TO-CONTROLLER MODE: we are bypassing the `unified_bridge`
ROS node (its running build is broken — every command crashes with
"'ClientConnection' object has no attribute 'closed'") and talking straight
to the TSP platform's controller websocket, the same endpoint unified_bridge
itself wraps: `ws://192.168.1.135:9000/terra_controller`. Protocol below was
reverse-engineered by probing the live controller + the covercrop
`test_drive.py` reference client, not from formal docs.

Wire protocol (confirmed against the live controller):

  - Envelope out: {"name": "<command>", "args": {...}}  (args omitted if empty)
  - Everything the controller sends carries a "topic" field. Two kinds:
      * unsolicited telemetry broadcasts — topics "gps", "battery",
        "temperature", "vesc", "TERRA_EVENT_TYPE_*". We ignore these.
      * command replies — topic "<command>_response", carrying:
            {"code": 0|-1, "return": {...}, "topic": "<command>_response"}
        code 0 = success, nonzero (seen: -1) = rejected. This is the ack.
  - Replies are async on the same socket, matched to requests by topic (there
    is no request id), so a background rx loop parses frames and hands each
    "<command>_response" to whoever is waiting on that topic. The controller
    sometimes splits one pretty-printed JSON object across frames, so rx
    buffers and re-parses (see `_drain_buf`).
  - getState reply (topic "getState_response") puts the robot state under
    `return`, including `is_emergency_stopped` and `led`. `_dispatch`
    promotes that to the top level of `last_status` so `dispatcher.py`
    (which reads `last_status["is_emergency_stopped"]`) doesn't change.

Two controller behaviours that matter:

  - MOTION HAS A WATCHDOG. `setNormalizedVehicleMotion` must be resent
    continuously (the reference client resends at 2 Hz); stop feeding it and
    the controller e-stops itself with "DRIVECMD_TIMEOUT REACHED". So a
    single motion send does nothing — `_motion_pulse` resends for the whole
    pulse, then sends zeros. There's also an "OPERATOR_TIMEOUT" e-stop source
    that an external operator heartbeat is expected to clear; feeding that,
    and releasing a latched e-stop, are out of scope here — while the robot
    is e-stopped, `dispatcher.py`'s safety gate refuses motion (correct).
  - Not every command necessarily replies. getState / *LED* commands do.
    startAutoMode / stopAutoMode / *EmergencyStop are assumed to but couldn't
    be tested safely, so `send_command` waits for the reply and, on timeout
    only, downgrades to "sent but unconfirmed" rather than failing. A reply
    that arrives with code != 0 is still surfaced as a real failure.

Remaining guesses, not yet confirmed against the real robot:

  - The `motion_pulse` speed/turnRate magnitudes and pulse duration
    (routes_config.py) are our own guess at a "brief nudge".
  - `startAutoMode`/`stopAutoMode` command names come from unified_bridge's
    mapping; not exercised against the live controller (would start real
    autonomous driving).
"""

import asyncio
import contextlib
import json
import logging
import time
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger("ebs.bridge_client")

# Topics the controller broadcasts unprompted; not command replies.
_TELEMETRY_TOPICS = {
    "gps",
    "battery",
    "temperature",
    "vesc",
    "TERRA_EVENT_TYPE_COLLECTION_UPDATE",
    "TERRA_EVENT_TYPE_SENSORS_STATUS_UPDATE",
}

# How often to resend the setpoint during a motion pulse. Must be well under
# the controller's drive-command watchdog timeout (else it self-e-stops).
_MOTION_KEEPALIVE_INTERVAL_S = 0.4


class BridgeError(Exception):
    """Raised when a command can't be delivered to (or is rejected by) the controller."""


class _ResponseTimeout(BridgeError):
    """A command was sent but no matching `<command>_response` arrived in time."""


class BridgeClient:
    """Persistent, auto-reconnecting websocket client to the TSP controller.

    Call `start()` once at app startup (kicks off a background connect + rx +
    status-poll loop) and `stop()` at shutdown. `send_command()` and
    `last_status` are safe to call at any time; they just reflect "not
    connected" until a connection is up.
    """

    def __init__(
        self,
        ws_url: str,
        reconnect_delay_s: float = 3.0,
        command_timeout_s: float = 5.0,
        status_poll_interval_s: float = 1.5,
    ):
        self._ws_url = ws_url
        self._reconnect_delay_s = reconnect_delay_s
        self._command_timeout_s = command_timeout_s
        self._status_poll_interval_s = status_poll_interval_s

        self._ws = None
        self._connected = asyncio.Event()
        self._last_status: dict[str, Any] | None = None
        self._last_status_at: float | None = None
        self._run_task: asyncio.Task | None = None
        self._send_lock = asyncio.Lock()
        self._waiters: dict[str, asyncio.Future] = {}
        self._rx_buf = ""

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        """Kick off the background connect/reconnect + rx + status-poll loop. Idempotent."""
        if self._run_task is None:
            self._run_task = asyncio.create_task(self._run_forever())

    async def stop(self) -> None:
        if self._run_task is not None:
            self._run_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._run_task
            self._run_task = None
        if self._ws is not None:
            with contextlib.suppress(Exception):
                await self._ws.close()
        self._connected.clear()

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    @property
    def last_status(self) -> dict[str, Any] | None:
        """Most recent getState `return` (with is_emergency_stopped at top
        level), or None if we haven't polled it successfully yet."""
        return self._last_status

    @property
    def last_status_age_s(self) -> float | None:
        if self._last_status_at is None:
            return None
        return time.time() - self._last_status_at

    # -- connection + rx + status-poll loop ---------------------------------

    async def _run_forever(self) -> None:
        while True:
            rx_task = None
            try:
                async with websockets.connect(self._ws_url, open_timeout=self._command_timeout_s) as ws:
                    self._ws = ws
                    self._rx_buf = ""
                    self._connected.set()
                    logger.info("connected to TSP controller at %s", self._ws_url)
                    rx_task = asyncio.create_task(self._rx_loop(ws))
                    await self._poll_status_forever()
            except (ConnectionClosed, OSError, BridgeError) as e:
                logger.warning("TSP controller connection lost/unavailable: %s", e)
            except Exception:
                logger.exception("unexpected error talking to the TSP controller")
            finally:
                self._connected.clear()
                self._ws = None
                if rx_task is not None:
                    rx_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await rx_task
                self._fail_waiters("lost connection to the TSP controller")
            await asyncio.sleep(self._reconnect_delay_s)

    async def _rx_loop(self, ws) -> None:
        async for frame in ws:
            self._rx_buf += frame
            self._drain_buf()

    def _drain_buf(self) -> None:
        """Parse every complete JSON object buffered so far and dispatch it.
        Leaves any trailing partial object in the buffer for the next frame."""
        while self._rx_buf.strip():
            try:
                obj, idx = json.JSONDecoder().raw_decode(self._rx_buf.lstrip())
            except ValueError:
                return  # incomplete — wait for more frames
            consumed = (len(self._rx_buf) - len(self._rx_buf.lstrip())) + idx
            self._rx_buf = self._rx_buf[consumed:]
            self._dispatch(obj)

    def _dispatch(self, obj: Any) -> None:
        if not isinstance(obj, dict):
            return
        topic = obj.get("topic")
        if topic is None or topic in _TELEMETRY_TOPICS:
            return

        if topic == "getState_response":
            ret = obj.get("return") or {}
            self._last_status = {
                **ret,
                "is_emergency_stopped": ret.get("is_emergency_stopped", False),
            }
            self._last_status_at = time.time()

        future = self._waiters.pop(topic, None)
        if future is not None and not future.done():
            future.set_result(obj)

    def _fail_waiters(self, reason: str) -> None:
        for future in self._waiters.values():
            if not future.done():
                future.set_exception(BridgeError(reason))
        self._waiters.clear()

    async def _poll_status_forever(self) -> None:
        """Keeps last_status fresh (the controller only reports e-stop state
        via getState, not in its telemetry broadcasts)."""
        while True:
            try:
                await self._send_and_wait("getState", None, "getState_response")
            except _ResponseTimeout as e:
                logger.debug("getState poll timed out: %s", e)
            # A send failure (closed socket) raises a plain BridgeError, which
            # propagates out to _run_forever and triggers a reconnect.
            await asyncio.sleep(self._status_poll_interval_s)

    # -- sending -------------------------------------------------------------

    async def _fire(self, name: str, args: dict | None = None) -> None:
        """Send a command without waiting for any reply (used for the motion
        keepalive, which resends far too often to await each ack)."""
        if not self.is_connected or self._ws is None:
            raise BridgeError("not connected to the TSP controller")
        msg: dict[str, Any] = {"name": name}
        if args:
            msg["args"] = args
        async with self._send_lock:
            try:
                await self._ws.send(json.dumps(msg))
            except (ConnectionClosed, OSError) as e:
                raise BridgeError(f"send '{name}' failed: {e}") from e

    async def _send_and_wait(
        self, name: str, args: dict | None, response_topic: str, timeout: float | None = None
    ) -> dict:
        """Send a command and wait for its `<name>_response`. Returns the
        response's `return` payload, or raises: _ResponseTimeout if no reply
        arrives, BridgeError if the reply's code is nonzero or the send fails."""
        if not self.is_connected or self._ws is None:
            raise BridgeError("not connected to the TSP controller")

        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._waiters[response_topic] = future

        msg: dict[str, Any] = {"name": name}
        if args:
            msg["args"] = args
        async with self._send_lock:
            try:
                await self._ws.send(json.dumps(msg))
            except (ConnectionClosed, OSError) as e:
                self._waiters.pop(response_topic, None)
                raise BridgeError(f"send '{name}' failed: {e}") from e

        try:
            resp = await asyncio.wait_for(future, timeout or self._command_timeout_s)
        except asyncio.TimeoutError as e:
            self._waiters.pop(response_topic, None)
            raise _ResponseTimeout(f"no {response_topic} within {timeout or self._command_timeout_s}s") from e

        code = resp.get("code")
        if code not in (None, 0):
            raise BridgeError(f"controller rejected '{name}' (code={code}): {resp.get('return')}")
        return resp.get("return", {}) or {}

    async def send_command(self, command: str, payload: dict | None = None) -> dict:
        """Dispatch a route's command to the controller.

        `command` is either the synthetic "motion_pulse" (see routes_config.py
        and `_motion_pulse`) or a raw controller command name
        (e.g. "startAutoMode", "stopAutoMode") sent as-is.
        """
        payload = payload or {}
        if command == "motion_pulse":
            return await self._motion_pulse(payload)

        response_topic = f"{command}_response"
        try:
            result = await self._send_and_wait(command, payload or None, response_topic)
            return {"confirmed": True, "result": result}
        except _ResponseTimeout:
            # The command may just not emit a reply; treat as sent. A real
            # rejection (code != 0) would have raised BridgeError instead.
            logger.warning("no %s from controller; treating '%s' as sent, unconfirmed", response_topic, command)
            return {"confirmed": False, "result": None}

    async def _motion_pulse(self, payload: dict) -> dict:
        """Drive at a fixed setpoint for `duration_s`, then stop. Resends the
        setpoint on an interval to keep the controller's drive watchdog fed
        (see module docstring), since a single send would immediately lapse."""
        speed = float(payload.get("speed", 0.0))
        turn_rate = float(payload.get("turnRate", payload.get("turn_rate", 0.0)))
        duration_s = float(payload.get("duration_s", 1.0))

        pulses = 0
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            await self._fire("setNormalizedVehicleMotion", {"speed": speed, "turnRate": turn_rate})
            pulses += 1
            await asyncio.sleep(_MOTION_KEEPALIVE_INTERVAL_S)

        # Explicitly park it — don't rely on the watchdog to stop the robot.
        for _ in range(3):
            await self._fire("setNormalizedVehicleMotion", {"speed": 0.0, "turnRate": 0.0})
            await asyncio.sleep(0.1)

        return {"pulses_sent": pulses, "speed": speed, "turnRate": turn_rate, "duration_s": duration_s}
