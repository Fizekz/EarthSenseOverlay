# EarthSenseOverlay

## Testing locally

Twitch extension views need to be served over HTTP(S). From `frontend/`:

```bash
cd frontend
python3 -m http.server 8080
```

Then open <http://localhost:8080/overlay.html> for a standalone preview.
