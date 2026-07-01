# ebs

The Extension Backend Service: the only piece of this repo that talks to the
TerraSentia Plus robot (`tsp-core-service`, documented in `../documentation.txt`).
`../bot` and `../overlay` both dispatch routes by calling this service instead
of talking to the robot directly — see the top-level README for the full
architecture diagram and why.

## Setup

```bash
cd ebs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in TWITCH_EXTENSION_SECRET and EBS_BOT_SHARED_SECRET
```

Run it:

```bash
set -a; source .env; set +a
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For local testing without a real robot, point `TSP_BASE_URL` at a mock/stub of
`tsp-core-service`, and set `EBS_DEV_MODE=true` to skip JWT verification (mirrors
the overlay's own "Local preview" fallback — never enable in production). See
the top-level README's "Local dry-testing" section for the matching overlay-side
fixtures.

## Deploying alongside `../bot` and `../overlay`

- `../bot` needs `EBS_BASE_URL` and `EBS_BOT_SHARED_SECRET` (same secret as this
  service's `.env`) set wherever it runs.
- `../overlay/js/overlay.js` needs `window.EBS_BASE_URL` set (e.g. in `overlay.html`,
  before `overlay.js` loads) to this service's deployed HTTPS URL. Twitch extension
  frontends are HTTPS-only and will block requests to a plain `http://` backend.
- Set `CORS_ALLOW_ORIGINS` in this service's `.env` to the extension's frontend
  origin so the browser doesn't block the request.

## Still to decide (see `app/routes_config.py`)

`ROUTES` currently has placeholder `mission_id`s. Fill in the real mission IDs
once they exist on the robot's `ag-manager` side, and `POST /ag_manager/mission/start`
will dispatch them as-is. If routes end up being raw waypoint lists instead of
predefined missions, `RouteDispatcher.dispatch()` currently raises
`RouteNotConfigured` for that case — the TSP docs don't specify how a waypoint
list actually starts moving (row-follow vs. sequential `navigation/goto` vs. a
generic "follow waypoints" mission), so `TspClient` needs a matching method once
that's settled.

Not implemented (out of scope for now, noted for later):
- Posting a "route dispatched" message back to Twitch chat when triggered from the
  overlay (Twitch's Helix "Send Extension Chat Message" endpoint) — needs its own
  extension-owner JWT signing, separate from the viewer JWT this service verifies.
- Any WebSocket subscription to `terra-controller`/`ag-manager` events (e.g. mission
  completion) — the busy-lock is currently a fixed timeout (`ROUTE_LOCK_SECONDS`)
  rather than a real "mission finished" signal.
