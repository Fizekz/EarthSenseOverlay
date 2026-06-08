# EarthSense Robot Routes — Twitch Extension Overlay

A Twitch **Video Overlay** extension that shows buttons for robot routes. Clicking
a route announces *"&lt;route&gt; is being executed."* The actual robot control and
real chat delivery are intentionally **not wired up yet** — this is the compliant
overlay scaffold.

## Current state

- ✅ Compliant overlay frontend (loads the Twitch helper, no inline scripts, transparent background).
- ✅ Three placeholder routes: **Route 1**, **Route 2**, **Route 3**.
- ✅ Click → in-overlay toast + status update.
- ✅ Broadcaster config page.
- ⏳ `sendRouteMessage()` is a **stub** — it logs instead of posting to chat. See below.
- ⏳ Robot route execution — to be added later.

## Files

```
frontend/
├── overlay.html      # Video → Overlay view (the on-stream UI)
├── config.html       # Broadcaster config view (required by Twitch)
├── css/
│   ├── style.css     # Overlay + shared styles (transparent background)
│   └── config.css    # Config page styles
└── js/
    ├── routes.js     # Route definitions — edit these
    ├── overlay.js    # Overlay logic + sendRouteMessage() stub
    └── config.js     # Config page logic
```

## Editing the routes

Everything lives in [`frontend/js/routes.js`](frontend/js/routes.js):

```js
window.ROBOT_ROUTES = [
  { id: 'route-1', name: 'Route 1', description: '...', icon: '①' },
  // ...
];
```

`id` is what gets sent to the backend later — keep it stable and URL-safe.

## Wiring real chat messages (later)

Twitch extensions can't post to chat directly from the frontend. You need an
**Extension Backend Service (EBS)** that signs an extension JWT and calls the Helix
[Send Extension Chat Message](https://dev.twitch.tv/docs/api/reference/#send-extension-chat-message)
endpoint. Your extension must also have the **"Send Chat Messages"** capability
enabled in the Twitch dev console.

Replace the stub in [`frontend/js/overlay.js`](frontend/js/overlay.js) (`sendRouteMessage`)
with a `fetch()` to your EBS — the commented example there shows the shape. Remember
to add your EBS domain to the extension's **Allowlist for URL Fetching Domains** in
the dev console, or Twitch's CSP will block the request.

## Testing locally

Twitch extension views need to be served over HTTP(S). From `frontend/`:

```bash
cd frontend
python3 -m http.server 8080
```

Then open <http://localhost:8080/overlay.html> for a standalone preview. Without the
Twitch context the status shows **"Local preview"** and clicks still produce toasts.

For a real in-Twitch test, use the
[Twitch Developer Rig](https://dev.twitch.tv/docs/extensions/rig/) or **Local Test**
hosting in the dev console, pointing the **Overlay** view at `overlay.html` and the
**Config** view at `config.html`.

## Packaging for upload

Twitch wants a zip of the frontend assets (HTML/CSS/JS at the archive root):

```bash
cd frontend && zip -r ../extension.zip . && cd ..
```

Upload `extension.zip` under **Asset Hosting** in the dev console.
