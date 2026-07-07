"""
Preset route -> Unified Bridge command mapping.

PROTOCOL TODO: `command` and `payload` are placeholders. The Unified Bridge
(built separately, on the robot) hasn't defined its drive/autonomy command
vocabulary yet — update these once that's settled. Until then dispatching
any route will fail at the bridge_client.send_command() step with a
BridgeError (no real bridge to ack it), which the dispatcher surfaces as a
503.

Ids match ../overlay/js/routes.js.
"""

ROUTES = {
    "route-1": {
        "name": "Route 1",
        "command": "TODO_ROUTE_1_COMMAND",
        "payload": {},
    },
    "route-2": {
        "name": "Route 2",
        "command": "TODO_ROUTE_2_COMMAND",
        "payload": {},
    },
    "route-3": {
        "name": "Route 3",
        "command": "TODO_ROUTE_3_COMMAND",
        "payload": {},
    },
}
