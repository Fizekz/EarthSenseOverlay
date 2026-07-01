import time

from .routes_config import ROUTES
from .tsp_client import TspClient


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
    """
    Owns the single source of truth for "is the robot busy" and "is this
    user on cooldown", so both the bot and the extension go through the same
    checks no matter which one triggers a route.

    There's no documented completion event for ag_manager missions, so the
    busy-lock is a timeout (route_lock_seconds) rather than a real
    "mission finished" signal — tune it to the longest route's expected
    duration, with some headroom.
    """

    def __init__(self, tsp_client: TspClient, route_lock_seconds: float = 120.0, user_cooldown_seconds: float = 60.0):
        self._tsp = tsp_client
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

        state = await self._tsp.controller_state()
        if state.get("is_emergency_stopped"):
            raise RobotUnsafe("robot is emergency-stopped, cannot dispatch a route")

        mission_id = route.get("mission_id")
        waypoints = route.get("waypoints")

        if mission_id:
            tsp_result = await self._tsp.start_mission(mission_id, route.get("params"))
        elif waypoints:
            raise RouteNotConfigured(
                "waypoint-based routes aren't wired up yet — see the 'waypoints' note in routes_config.py"
            )
        else:
            raise RouteNotConfigured(f"route '{route_id}' has no mission_id or waypoints configured yet")

        self._busy_until = now + self._route_lock_seconds
        self._busy_route = route_id
        self._last_trigger[user_id] = now

        return {
            "route_id": route_id,
            "name": route["name"],
            "dispatched_by": user_name,
            "source": source,
            "tsp_result": tsp_result,
        }
