"""
Preset route -> TSP dispatch mapping. Each entry needs mission_id or waypoints:
  - mission_id: POST /ag_manager/mission/start {mission_id, params}.
  - waypoints: not wired up yet (RouteDispatcher raises RouteNotConfigured) —
    TSP docs don't say how a waypoint list starts moving.

Ids match ../overlay/js/routes.js and the !route1/2/3 commands in ../bot.
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
