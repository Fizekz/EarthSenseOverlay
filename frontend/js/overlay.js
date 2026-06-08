/*
 * Overlay logic for the EarthSense robot-route Twitch Extension.
 *
 * Responsibilities:
 *   - Render a button per route from window.ROBOT_ROUTES.
 *   - On click, show an in-overlay toast and call sendRouteMessage().
 *   - sendRouteMessage() is currently a STUB: it does not hit a backend yet.
 *     When the EBS exists, replace the body with a fetch() to it (see below).
 *
 * No inline scripts / handlers are used, to stay friendly with the strict
 * Content-Security-Policy that Twitch enforces on extension frontends.
 */
(function () {
  'use strict';

  var routesEl = document.getElementById('routes');
  var toastsEl = document.getElementById('toasts');
  var statusEl = document.getElementById('status');
  var routes = window.ROBOT_ROUTES || [];

  // Populated by Twitch.ext.onAuthorized once the extension is authorized.
  // Holds { channelId, clientId, token, userId, ... }. Used later by the EBS call.
  var auth = null;

  function setStatus(text, state) {
    statusEl.textContent = text;
    statusEl.setAttribute('data-state', state || 'idle');
  }

  function showToast(message) {
    var toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toastsEl.appendChild(toast);

    // Animate in on the next frame so the transition runs.
    requestAnimationFrame(function () { toast.classList.add('toast--show'); });

    window.setTimeout(function () {
      toast.classList.remove('toast--show');
      window.setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
  }

  /*
   * STUB. Pretends to send "<route> is being executed" to chat.
   *
   * Real implementation (later): POST to your EBS, which signs an extension
   * JWT and calls the Helix "Send Extension Chat Message" endpoint:
   *
   *   if (!auth) return Promise.reject(new Error('Not authorized'));
   *   return fetch(EBS_BASE + '/routes/execute', {
   *     method: 'POST',
   *     headers: {
   *       'Content-Type': 'application/json',
   *       'Authorization': 'Bearer ' + auth.token
   *     },
   *     body: JSON.stringify({ routeId: route.id })
   *   }).then(function (res) {
   *     if (!res.ok) throw new Error('EBS responded ' + res.status);
   *     return res.json();
   *   });
   */
  function sendRouteMessage(route) {
    var message = 'Executing ' + route.name + ' — route is being executed';
    // eslint-disable-next-line no-console
    console.log('[stub] would post to chat:', message, '| authorized:', !!auth);
    return Promise.resolve({ ok: true, stub: true, message: message });
  }

  function executeRoute(route, button) {
    button.disabled = true;
    setStatus('Executing: ' + route.name, 'busy');
    showToast(route.icon + '  ' + route.name + ' is being executed');

    sendRouteMessage(route)
      .then(function () {
        setStatus('Sent: ' + route.name, 'ok');
      })
      .catch(function (err) {
        // eslint-disable-next-line no-console
        console.warn('Route send failed:', err);
        setStatus('Failed: ' + route.name, 'warn');
      })
      .then(function () {
        button.disabled = false;
        window.setTimeout(function () { setStatus('Idle', 'idle'); }, 2500);
      });
  }

  function renderRoutes() {
    if (!routes.length) {
      var empty = document.createElement('p');
      empty.className = 'routes__empty';
      empty.textContent = 'No routes configured.';
      routesEl.appendChild(empty);
      return;
    }

    routes.forEach(function (route) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'route';
      btn.setAttribute('aria-label', 'Execute ' + route.name);

      var icon = document.createElement('span');
      icon.className = 'route__icon';
      icon.textContent = route.icon || '▶';

      var body = document.createElement('span');
      body.className = 'route__body';

      var name = document.createElement('span');
      name.className = 'route__name';
      name.textContent = route.name;

      var desc = document.createElement('span');
      desc.className = 'route__desc';
      desc.textContent = route.description || '';

      body.appendChild(name);
      body.appendChild(desc);
      btn.appendChild(icon);
      btn.appendChild(body);

      btn.addEventListener('click', function () { executeRoute(route, btn); });
      routesEl.appendChild(btn);
    });
  }

  renderRoutes();

  // Wire up the Twitch helper when present; degrade gracefully for local preview.
  if (window.Twitch && window.Twitch.ext) {
    window.Twitch.ext.onAuthorized(function (authData) {
      auth = authData;
      setStatus('Connected', 'ok');
      window.setTimeout(function () { setStatus('Idle', 'idle'); }, 1500);
    });
  } else {
    setStatus('Local preview', 'warn');
  }
})();
