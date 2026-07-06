# EarthSense

Twitch integrations for dispatching an EarthSense robot (TerraSentia Plus / TSP)
on preset routes, from chat or a viewer overlay.

```
Twitch chat    ──!route1──▶  bot/     ──POST /internal/routes/:id/execute──┐
                                                                             ▼
Twitch overlay ──click───▶  overlay/  ──POST /routes/:id/execute────▶   ebs/ ──▶ tsp-core-service
```

## Layout

- `bot/` — twitchio chat bot. `!route1/2/3` call the EBS. Possible future deprecation
- `overlay/` — Twitch Video Overlay Extension frontend.
- `ebs/` — Extension Backend Service, bridges Twitch Extension with `tsp-core`. **WIP** (See `ebs/README.md`).

## Status

**Still Testing**

Full pipeline confirmed working end-to-end against a Hosted Test extension and a stubbed
`tsp-core-service`. Still open:

- `ebs/app/routes_config.py` routes use placeholder `mission_id`s
- `ebs/`'s current deployment is a local dev server behind a Cloudflare quick
  tunnel
  - The extension's "Allowlist for URL Fetching Domains" (Developer Console →
  Capabilities) must match whatever's actually set as `EBS_BASE_URL`
- `EBS_DEV_MODE` must be `false` (with a real `TWITCH_EXTENSION_SECRET`)

See `ebs/README.md` for the rest.
