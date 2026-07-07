import time

from .bridge_client import BridgeClient, BridgeError
from .routes_config import ROUTES


class RouteError(Exception):
    http_status = 400


class UnknownRoute(RouteError):
    http_status = 404


class RouteBusy(RouteError):
    http_status = 409


class OnCooldown(RouteError):
    http_status = 429


class RouteNotConfigured(RouteError):
    http_status = 501


class RobotUnsafe(RouteError):
    http_status = 503


class RouteDispatcher:
    """Shared busy-lock + per-user cooldown for route dispatches from the overlay.

    No completion event exists for Unified Bridge commands yet (that's a
    PROTOCOL TODO in bridge_client.py too), so the lock is a timeout
    (route_lock_seconds), not a real "route finished" signal.
    """

    def __init__(self, bridge: BridgeClient, route_lock_seconds: float = 120.0, user_cooldown_seconds: float = 60.0):
        self._bridge = bridge
        self._route_lock_seconds = route_lock_seconds
        self._user_cooldown_seconds = user_cooldown_seconds
        self._busy_until = 0.0
        self._busy_route = None
        self._last_trigger: dict[str, float] = {}

    def list_routes(self):
        return [{"id": route_id, "name": route["name"]} for route_id, route in ROUTES.items()]

    async def dispatch(self, route_id: str, user_id: str, user_name: str, source: str) -> dict:
        route = ROUTES.get(route_id)
        if route is None:
            raise UnknownRoute(f"unknown route '{route_id}'")

        now = time.time()

        if now < self._busy_until:
            raise RouteBusy(
                f"robot is busy running '{self._busy_route}', try again in {int(self._busy_until - now)}s"
            )

        last = self._last_trigger.get(user_id)
        if last is not None and (now - last) < self._user_cooldown_seconds:
            raise OnCooldown(
                f"on cooldown, try again in {int(self._user_cooldown_seconds - (now - last))}s"
            )

        if not self._bridge.is_connected:
            raise RobotUnsafe("not connected to the robot's Unified Bridge")

        status = self._bridge.last_status or {}
        if status.get("is_emergency_stopped"):
            raise RobotUnsafe("robot is emergency-stopped, cannot dispatch a route")

        command = route.get("command")
        payload = route.get("payload")

        if not command:
            raise RouteNotConfigured(f"route '{route_id}' has no command configured yet")

        try:
            bridge_result = await self._bridge.send_command(command, payload)
        except BridgeError as e:
            raise RobotUnsafe(f"Unified Bridge rejected/failed the command: {e}") from e

        self._busy_until = now + self._route_lock_seconds
        self._busy_route = route_id
        self._last_trigger[user_id] = now

        return {
            "route_id": route_id,
            "name": route["name"],
            "dispatched_by": user_name,
            "source": source,
            "bridge_result": bridge_result,
        }
