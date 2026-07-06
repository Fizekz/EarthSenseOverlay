# ebs

Extension Backend Service — the only piece of this repo that talks to the
TSP robot (`tsp-core-service`). `../bot` and `../overlay` dispatch routes
through this service instead of calling the robot directly (see top-level
README for why).

## Setup

```bash
cd ebs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in TWITCH_EXTENSION_SECRET and EBS_BOT_SHARED_SECRET
set -a; source .env; set +a
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For local testing without a real robot: point `TSP_BASE_URL` at a stub, and set
`EBS_DEV_MODE=true` to skip JWT verification (never enable in production).

## Deploying with `../bot` and `../overlay`

- `../bot` needs `EBS_BASE_URL` and `EBS_BOT_SHARED_SECRET` (same secret as here).
- `../overlay/js/overlay.js` needs `window.EBS_BASE_URL` set to this service's
  HTTPS URL — extension frontends are HTTPS-only.
- `CORS_ALLOW_ORIGINS` should match the extension's frontend origin.
