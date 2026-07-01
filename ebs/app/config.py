import os


class Settings:
    def __init__(self):
        self.tsp_base_url = os.environ.get("TSP_BASE_URL", "http://localhost:8080")
        self.tsp_timeout_s = float(os.environ.get("TSP_TIMEOUT_S", "5.0"))

        self.twitch_extension_secret = os.environ.get("TWITCH_EXTENSION_SECRET", "")
        self.bot_shared_secret = os.environ.get("EBS_BOT_SHARED_SECRET", "")

        self.cors_allow_origins = [
            o.strip()
            for o in os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")
            if o.strip()
        ]

        self.dev_mode = os.environ.get("EBS_DEV_MODE", "false").lower() == "true"

        self.route_lock_seconds = float(os.environ.get("ROUTE_LOCK_SECONDS", "120"))
        self.user_cooldown_seconds = float(os.environ.get("USER_COOLDOWN_SECONDS", "60"))


settings = Settings()
