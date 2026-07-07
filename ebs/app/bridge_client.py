"""
Websocket client for the robot's Unified Bridge.

STUB — read this before touching dispatch logic.

There is no "tsp-core-sdk" to import here. EBS does not POST to a
tsp-core-service and never did in practice; that was an earlier, incorrect
assumption baked into the old `tsp_client.py`. The real design is:

  - The robot is not on the internet. It hosts its own wifi network.
  - This EBS machine is wired to ethernet (for Twitch/internet) and also
    joins the robot's wifi to reach it locally.
  - A separate AI agent is building the "Unified Bridge" that runs *on* the
    robot and talks to Robot Services (see whiteboard diagram: Unified
    Bridge <-> Robot Services, cmds/events).
  - EBS <-> Unified Bridge happens over a plain websocket. This module is
    EBS's side of that connection.

Client/server direction (judgment call, not yet confirmed with the robot
side): the robot hosts the wifi network it's reachable on, so it's the
stable, discoverable end — the Unified Bridge should run the websocket
*server*, and EBS (this module) is the *client* that dials in and
reconnects if the link drops. That's the assumption baked in below. If the
other agent's implementation ends up flipped (Unified Bridge dials out to
EBS instead), this module needs to become a server instead — everything
above the transport (message shapes, dispatcher usage) stays the same
either way.

Everything below — message envelope, field names, command vocabulary,
whether acks even exist — is a PLACEHOLDER guess at a protocol that hasn't
been defined yet. Every such guess is tagged `PROTOCOL TODO` below. None of
it should be treated as load-bearing until it's been reconciled against
whatever the Unified Bridge actually speaks.
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


class BridgeError(Exception):
    """Raised when a command can't be delivered to (or acked by) the Unified Bridge."""


class BridgeClient:
    """Persistent, auto-reconnecting websocket client to the robot's Unified Bridge.

    Call `start()` once at app startup (kicks off a background connect loop)
    and `stop()` at shutdown. `send_command()` and `last_status` are safe to
    call at any time; they just reflect "not connected" until a connection
    is up.
    """

    def __init__(
        self,
        ws_url: str,
        reconnect_delay_s: float = 3.0,
        command_timeout_s: float = 5.0,
    ):
        self._ws_url = ws_url
        self._reconnect_delay_s = reconnect_delay_s
        self._command_timeout_s = command_timeout_s

        self._ws = None
        self._connected = asyncio.Event()
        self._last_status: dict[str, Any] | None = None
        self._last_status_at: float | None = None
        self._run_task: asyncio.Task | None = None
        self._pending_acks: dict[str, asyncio.Future] = {}

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        """Kick off the background connect/reconnect loop. Idempotent."""
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
        """Most recent status_update payload from the bridge, or None if we
        haven't received one yet (e.g. never connected)."""
        return self._last_status

    @property
    def last_status_age_s(self) -> float | None:
        if self._last_status_at is None:
            return None
        return time.time() - self._last_status_at

    # -- connection loop -----------------------------------------------------

    async def _run_forever(self) -> None:
        while True:
            try:
                async with websockets.connect(self._ws_url) as ws:
                    self._ws = ws
                    self._connected.set()
                    logger.info("connected to Unified Bridge at %s", self._ws_url)
                    await self._listen(ws)
            except (ConnectionClosed, OSError) as e:
                logger.warning("Unified Bridge connection lost/unavailable: %s", e)
            except Exception:
                logger.exception("unexpected error talking to the Unified Bridge")
            finally:
                self._connected.clear()
                self._ws = None
                self._fail_pending_acks("lost connection to the Unified Bridge")
            await asyncio.sleep(self._reconnect_delay_s)

    async def _listen(self, ws) -> None:
        async for raw in ws:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("non-JSON message from Unified Bridge: %r", raw)
                continue
            self._handle_message(message)

    def _handle_message(self, message: dict) -> None:
        # PROTOCOL TODO: real envelope/type names come from the Unified
        # Bridge implementation. Guessing a `{"type": ..., ...}` envelope
        # with "status_update" and "ack" as the two message kinds EBS cares
        # about; the robot side may also push other event types (see
        # "events" arrow from Robot Services on the whiteboard) that aren't
        # modeled here yet.
        msg_type = message.get("type")

        if msg_type == "status_update":
            self._last_status = message.get("data", {})
            self._last_status_at = time.time()
        elif msg_type == "ack":
            request_id = message.get("request_id")
            future = self._pending_acks.pop(request_id, None)
            if future is not None and not future.done():
                future.set_result(message)
        else:
            logger.debug("unhandled Unified Bridge message type: %r", msg_type)

    def _fail_pending_acks(self, reason: str) -> None:
        for future in self._pending_acks.values():
            if not future.done():
                future.set_exception(BridgeError(reason))
        self._pending_acks.clear()

    # -- commands ------------------------------------------------------------

    async def send_command(self, command: str, payload: dict | None = None) -> dict:
        """Send a drive/autonomy command to the Unified Bridge and wait for an ack.

        PROTOCOL TODO: request/ack envelope, field names, and whether the
        bridge even acks commands (vs. fire-and-forget + status_update as
        the only feedback) are all placeholders. Update once the real
        Unified Bridge protocol is known.
        """
        if not self.is_connected or self._ws is None:
            raise BridgeError("not connected to the robot's Unified Bridge")

        request_id = f"{command}-{time.time_ns()}"
        message = {
            "type": "command",
            "command": command,
            "payload": payload or {},
            "request_id": request_id,
        }

        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._pending_acks[request_id] = future
        try:
            await self._ws.send(json.dumps(message))
            return await asyncio.wait_for(future, timeout=self._command_timeout_s)
        except asyncio.TimeoutError as e:
            raise BridgeError(
                f"no ack from Unified Bridge for '{command}' within {self._command_timeout_s}s"
            ) from e
        finally:
            self._pending_acks.pop(request_id, None)
