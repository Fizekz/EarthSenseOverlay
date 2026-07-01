# EarthSense

Twitch integrations for controlling an EarthSense robot (TerraSentia Plus / TSP
platform) on preset routes — either from chat or from a viewer-facing overlay.

```
Twitch chat  ──!route1──▶  bot/       ──POST /internal/routes/:id/execute──┐
                                            (X-EBS-Secret header)           │
                                                                             ▼
Twitch overlay ──click──▶  overlay/   ──POST /routes/:id/execute──▶     ebs/
                              (Authorization: Bearer <extension JWT>)       │
                                                                             ▼
                                                                 tsp-core-service
                                                                 (robot's REST API)
```

## Layout

- `bot/` — the Twitch chat bot (`twitchio`). `!route1/2/3` commands call the EBS.
- `overlay/` — the Twitch Video Overlay Extension frontend (viewer-facing route
  buttons + broadcaster config page). Rendered by Twitch's player per-viewer;
  not something OBS composites into the video.
- `ebs/` — the Extension Backend Service. The only thing that talks to the
  robot. Owns the shared busy-lock and per-user cooldown so a chat command and
  an overlay click can't dispatch the robot at the same time. See `ebs/README.md`
  for the architecture and setup.

## Why one shared backend

`bot/` and `overlay/` are two independent processes/contexts with no shared
state. If each called `tsp-core-service` directly, they'd each need their own
cooldown/lock tracking, and a chat command racing an overlay click could
dispatch the robot twice at once. Routing both through `ebs/` makes the lock
and cooldown real.

## Local dry-testing (no real robot / no real Twitch)

`overlay/overlay.local-test.html` and `overlay/js/mock-twitch-ext.local-test.js`
stand in for the real Twitch Extension Helper so you can click-test the overlay
in a plain browser, against a locally running `ebs/` (set `EBS_DEV_MODE=true` to
skip real JWT verification) and a stub of `tsp-core-service`. These two files
are dev-only fixtures — never reference them from the real `overlay.html`.

For the real extension frontend:

```bash
cd overlay
python3 -m http.server 8080
```

Then open <http://localhost:8080/overlay.html> for a standalone (unauthenticated)
preview — it'll show "Local preview" status since there's no real Twitch iframe.

## Status

Preset routes in `ebs/app/routes_config.py` currently use placeholder
`mission_id`s — fill in the real ones once they exist on the robot's
`ag-manager` side. See `ebs/README.md` for what's still open (waypoint-based
routes, chat feedback on overlay-triggered dispatches, mission-completion
events).
