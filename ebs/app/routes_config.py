"""
Preset route -> TSP dispatch mapping.

Each entry needs exactly one of "mission_id" or "waypoints" populated:

  - mission_id: dispatched as POST /ag_manager/mission/start {mission_id, params}.
    Use this once the robot has predefined missions for these routes.

  - waypoints: a list of {id, lat, lon, heading?} objects. NOT wired up yet —
    the TSP docs don't specify how a waypoint list transitions into motion
    (row_follow vs. sequential navigation/goto vs. a dedicated mission id),
    so RouteDispatcher raises RouteNotConfigured until that's decided and
    TspClient grows a matching method.

route-1/2/3 ids match window.ROBOT_ROUTES in EarthSenseOverlay's routes.js
and the !route1/2/3 command names in EarthSenseBot's twitch_bot.py.
"""

ROUTES = {
    "route-1": {
        "name": "Route 1",
        "mission_id": "TODO_ROUTE_1_MISSION_ID",
        "params": {},
        "waypoints": None,
    },
    "route-2": {
        "name": "Route 2",
        "mission_id": "TODO_ROUTE_2_MISSION_ID",
        "params": {},
        "waypoints": None,
    },
    "route-3": {
        "name": "Route 3",
        "mission_id": "TODO_ROUTE_3_MISSION_ID",
        "params": {},
        "waypoints": None,
    },
}
