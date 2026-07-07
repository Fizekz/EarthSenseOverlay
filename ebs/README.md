# ebs

Extension Backend Service — the only piece of this repo that talks to the
robot. `../overlay` dispatches routes through this service instead of
calling the robot directly (see top-level README for why).

EBS talks to the robot's **Unified Bridge** over a websocket — not a REST
API, and not a "tsp-core-sdk" (there isn't one; that was an earlier,
incorrect assumption). The Unified Bridge is being built by a separate
effort on the robot side, so `app/bridge_client.py` is currently a stub:
connection handling is real, but the message protocol (envelope, command
names, ack shape) is a guessed placeholder until the real bridge exists.
See the comments at the top of that file before changing dispatch behavior.

## Setup

```bash
cd ebs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in TWITCH_EXTENSION_SECRET
set -a; source .env; set +a
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For local testing without a real robot: point `BRIDGE_WS_URL` at any
websocket server that speaks the placeholder protocol in
`bridge_client.py` (or leave it — EBS will just log reconnect attempts and
report `bridge_connected: false` from `/health`), and set `EBS_DEV_MODE=true`
to skip JWT verification (never enable in production).

## Network layout

The robot isn't on the internet; it hosts its own wifi network. This
service's machine (the "OBS Machine" in the whiteboard diagram) is wired to
ethernet for internet/Twitch access and also joins the robot's wifi to reach
the Unified Bridge. `BRIDGE_WS_URL` should point at the robot's address on
that wifi network (e.g. `ws://192.168.4.1:8765/ws` — placeholder, confirm
against the real Unified Bridge deployment).

## Deploying with `../overlay`

- `../overlay/js/overlay.js` needs `window.EBS_BASE_URL` set to this
  service's HTTPS URL — extension frontends are HTTPS-only.
- `CORS_ALLOW_ORIGINS` should match the extension's frontend origin.
