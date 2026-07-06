# EarthSense

Twitch integrations for dispatching an EarthSense robot (TerraSentia Plus / TSP)
on preset routes, from chat or a viewer overlay.

```
Twitch chat    ──!route1──▶  bot/     ──POST /internal/routes/:id/execute──┐
                                                                             ▼
Twitch overlay ──click───▶  overlay/  ──POST /routes/:id/execute────▶   ebs/ ──▶ tsp-core-service
```

## Layout

- `bot/` — twitchio chat bot. `!route1/2/3` call the EBS.
- `overlay/` — Twitch Video Overlay Extension frontend. Rendered per-viewer by
  Twitch's player, not by OBS.
- `ebs/` — Extension Backend Service, the only thing that talks to the robot.
  Shared busy-lock + per-user cooldown so bot and overlay can't dispatch at
  once. See `ebs/README.md`.

## Local dry-testing

`overlay/overlay.local-test.html` + `overlay/js/mock-twitch-ext.local-test.js`
mock the Twitch Extension Helper for click-testing in a plain browser against
a local `ebs/` (`EBS_DEV_MODE=true` skips JWT verification) and a stubbed
`tsp-core-service`. Dev-only — never reference from the real `overlay.html`.

For the real frontend: `cd overlay && python3 -m http.server 8080`, then open
`overlay.html` for an unauthenticated "Local preview".

## Status

Full pipeline (overlay click → EBS auth/busy-lock/cooldown → TSP dispatch)
confirmed working end-to-end against a Hosted Test extension and a stubbed
`tsp-core-service`. Still open:

- `ebs/app/routes_config.py` routes use placeholder `mission_id`s — fill in
  the real ones once defined on the robot.
- `ebs/`'s current deployment is a local dev server behind a Cloudflare quick
  tunnel — fine for testing, not durable enough for review/submission or a
  live stream. Needs a real always-on host before then.
- `EBS_DEV_MODE` must be `false` (with a real `TWITCH_EXTENSION_SECRET`)
  before this ever points at an actual robot — it currently skips JWT
  verification.
- The extension's "Allowlist for URL Fetching Domains" (Developer Console →
  Capabilities) must match whatever's actually set as `EBS_BASE_URL`, or the
  overlay's requests fail via CSP, not a network error.

See `ebs/README.md` for the rest.
