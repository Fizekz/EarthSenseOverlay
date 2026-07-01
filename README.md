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

`ebs/app/routes_config.py` routes use placeholder `mission_id`s — fill in the
real ones once defined on the robot. See `ebs/README.md` for open items.
