"""
Route id -> TSP controller command mapping.

TEMPORARY DIRECT-TO-CONTROLLER MODE: these map to the raw TSP controller
command names sent straight over the terra_controller websocket (we're
bypassing the broken unified_bridge — see bridge_client.py's module
docstring). There's no "preset route" concept on the controller — just
continuous motion, auto mode, and e-stop.

forward/backward use the synthetic "motion_pulse" command, which
bridge_client.py turns into repeated `setNormalizedVehicleMotion` sends for
`duration_s` (to feed the controller's drive watchdog) followed by zeros to
stop. `PULSE_SPEED`/`PULSE_DURATION_S` are our own guess at a "brief nudge"
magnitude/duration — not from any spec; adjust once seen on the real robot.
`PULSE_DURATION_S` should stay roughly in sync with `ROUTE_LOCK_SECONDS`
(config.py / .env). Note `turnRate` is the controller's camelCase arg name.

auto-start/auto-stop map to the controller's `startAutoMode`/`stopAutoMode`
commands (names via unified_bridge's mapping), no args. These will only take
effect when the robot isn't e-stopped; while it is, dispatcher.py's safety
gate refuses them (503).

Ids match ../overlay/js/routes.js.
"""

PULSE_SPEED = 0.4
PULSE_DURATION_S = 1.5

ROUTES = {
    "forward": {
        "name": "Forward",
        "command": "motion_pulse",
        "payload": {"speed": PULSE_SPEED, "turnRate": 0.0, "duration_s": PULSE_DURATION_S},
    },
    "backward": {
        "name": "Backward",
        "command": "motion_pulse",
        "payload": {"speed": -PULSE_SPEED, "turnRate": 0.0, "duration_s": PULSE_DURATION_S},
    },
    "auto-start": {
        "name": "Start Auto Mode",
        "command": "startAutoMode",
        "payload": {},
    },
    "auto-stop": {
        "name": "Stop Auto Mode",
        "command": "stopAutoMode",
        "payload": {},
    },
}
