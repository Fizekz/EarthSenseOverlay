/*
 * EBS base URL for the deployed extension, read by overlay.js.
 *
 * Twitch's extension CSP forbids inline scripts, so this can't be an inline
 * <script> in overlay.html (the way overlay.local-test.html does it for local
 * dev) — it has to be its own file.
 *
 * This committed value is a PLACEHOLDER. The package script
 * (overlay/package.sh) rewrites it with the real HTTPS EBS URL at package
 * time, and refuses to build a zip that still contains the placeholder — so
 * this string never ships as-is.
 */
window.EBS_BASE_URL = 'https://YOUR-EBS-URL-HERE';
