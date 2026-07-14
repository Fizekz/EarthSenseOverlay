import os


class Settings:
    def __init__(self):
        # Websocket URL for the robot, reachable over the robot's own wifi
        # network (this machine is wired to ethernet and also joins that
        # wifi). TEMPORARY DIRECT-TO-CONTROLLER MODE: pointed straight at the
        # TSP controller's terra_controller socket, bypassing the broken
        # unified_bridge (see bridge_client.py's module docstring). If/when
        # unified_bridge is fixed, this goes back to ws://<bridge-host>:9100.
        self.bridge_ws_url = os.environ.get("BRIDGE_WS_URL", "ws://192.168.1.135:9000/terra_controller")
        self.bridge_reconnect_delay_s = float(os.environ.get("BRIDGE_RECONNECT_DELAY_S", "3.0"))
        self.bridge_command_timeout_s = float(os.environ.get("BRIDGE_COMMAND_TIMEOUT_S", "5.0"))
        self.bridge_status_poll_interval_s = float(os.environ.get("BRIDGE_STATUS_POLL_INTERVAL_S", "1.5"))

        self.twitch_extension_secret = os.environ.get("TWITCH_EXTENSION_SECRET", "")

        self.cors_allow_origins = [
            o.strip()
            for o in os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")
            if o.strip()
        ]

        self.dev_mode = os.environ.get("EBS_DEV_MODE", "false").lower() == "true"

        # TEMPORARY defaults sized for the forward/backward drive-pulse test
        # in routes_config.py (PULSE_DURATION_S=1.5s), not real preset
        # routes — bump these back up once routes_config.py goes back to
        # longer-running routes.
        self.route_lock_seconds = float(os.environ.get("ROUTE_LOCK_SECONDS", "2"))
        self.user_cooldown_seconds = float(os.environ.get("USER_COOLDOWN_SECONDS", "2"))


settings = Settings()
