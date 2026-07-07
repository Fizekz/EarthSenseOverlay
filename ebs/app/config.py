import os


class Settings:
    def __init__(self):
        # Websocket URL for the robot's Unified Bridge, reachable over the
        # robot's own wifi network (this machine is wired to ethernet and
        # also joins that wifi — see bridge_client.py for the full picture).
        # PLACEHOLDER default — set to wherever the Unified Bridge actually
        # listens once that's stood up.
        self.bridge_ws_url = os.environ.get("BRIDGE_WS_URL", "ws://192.168.4.1:8765/ws")
        self.bridge_reconnect_delay_s = float(os.environ.get("BRIDGE_RECONNECT_DELAY_S", "3.0"))
        self.bridge_command_timeout_s = float(os.environ.get("BRIDGE_COMMAND_TIMEOUT_S", "5.0"))

        self.twitch_extension_secret = os.environ.get("TWITCH_EXTENSION_SECRET", "")

        self.cors_allow_origins = [
            o.strip()
            for o in os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")
            if o.strip()
        ]

        self.dev_mode = os.environ.get("EBS_DEV_MODE", "false").lower() == "true"

        self.route_lock_seconds = float(os.environ.get("ROUTE_LOCK_SECONDS", "120"))
        self.user_cooldown_seconds = float(os.environ.get("USER_COOLDOWN_SECONDS", "60"))


settings = Settings()
