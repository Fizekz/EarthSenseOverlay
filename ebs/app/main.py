from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .bridge_client import BridgeClient
from .config import settings
from .dispatcher import RouteDispatcher, RouteError
from .twitch_auth import TwitchAuthError, verify_extension_jwt

bridge = BridgeClient(
    settings.bridge_ws_url,
    reconnect_delay_s=settings.bridge_reconnect_delay_s,
    command_timeout_s=settings.bridge_command_timeout_s,
)
dispatcher = RouteDispatcher(
    bridge,
    route_lock_seconds=settings.route_lock_seconds,
    user_cooldown_seconds=settings.user_cooldown_seconds,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    bridge.start()
    try:
        yield
    finally:
        await bridge.stop()


app = FastAPI(title="EarthSense EBS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
async def health():
    return {
        "ebs": "ok",
        "bridge_connected": bridge.is_connected,
        "bridge_last_status": bridge.last_status,
        "bridge_last_status_age_s": bridge.last_status_age_s,
    }


@app.get("/routes")
async def list_routes():
    return {"routes": dispatcher.list_routes()}


@app.post("/routes/{route_id}/execute")
async def execute_from_extension(route_id: str, authorization: str = Header(...)):
    """Called by ../overlay, authenticated with a Twitch extension JWT."""
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = verify_extension_jwt(token, settings.twitch_extension_secret, dev_mode=settings.dev_mode)
    except TwitchAuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    user_id = claims.get("user_id") or claims.get("opaque_user_id")
    try:
        return await dispatcher.dispatch(route_id, user_id=user_id, user_name=user_id, source="extension")
    except RouteError as e:
        raise HTTPException(status_code=e.http_status, detail=str(e)) from e
