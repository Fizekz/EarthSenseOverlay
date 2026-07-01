from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .dispatcher import RouteDispatcher, RouteError
from .tsp_client import TspClient
from .twitch_auth import TwitchAuthError, verify_extension_jwt

app = FastAPI(title="EarthSense EBS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-EBS-Secret"],
)

tsp_client = TspClient(settings.tsp_base_url, settings.tsp_timeout_s)
dispatcher = RouteDispatcher(
    tsp_client,
    route_lock_seconds=settings.route_lock_seconds,
    user_cooldown_seconds=settings.user_cooldown_seconds,
)


class BotExecuteRequest(BaseModel):
    user_id: str
    user_name: str


@app.get("/health")
async def health():
    try:
        tsp_health = await tsp_client.health()
    except Exception as e:
        return {"ebs": "ok", "tsp": "unreachable", "error": str(e)}
    return {"ebs": "ok", "tsp": tsp_health}


@app.get("/routes")
async def list_routes():
    return {"routes": dispatcher.list_routes()}


@app.post("/routes/{route_id}/execute")
async def execute_from_extension(route_id: str, authorization: str = Header(...)):
    """Called by the EarthSenseOverlay frontend, authenticated with the Twitch extension JWT."""
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


@app.post("/internal/routes/{route_id}/execute")
async def execute_from_bot(route_id: str, body: BotExecuteRequest, x_ebs_secret: str = Header(...)):
    """Called by EarthSenseBot, authenticated with a shared secret (see .env.example)."""
    if not settings.bot_shared_secret or x_ebs_secret != settings.bot_shared_secret:
        raise HTTPException(status_code=401, detail="invalid shared secret")

    try:
        return await dispatcher.dispatch(route_id, user_id=body.user_id, user_name=body.user_name, source="bot")
    except RouteError as e:
        raise HTTPException(status_code=e.http_status, detail=str(e)) from e
