/*
 * Overlay logic for the EarthSense robot-route Twitch Extension.
 *
 * Responsibilities:
 *   - Render a button per route from window.ROBOT_ROUTES.
 *   - On click, show an in-overlay toast and call sendRouteMessage().
 *   - sendRouteMessage() calls the EarthSense EBS (see ../ebs/), which
 *     verifies the Twitch extension JWT, applies the busy-lock and
 *     per-user cooldown, and dispatches the robot.
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

  // Deployed EBS base URL. Must be HTTPS in production (Twitch extension
  // frontends are served over HTTPS and will block mixed-content requests).
  var EBS_BASE_URL = window.EBS_BASE_URL || 'https://localhost:8000';

  // Populated by Twitch.ext.onAuthorized once the extension is authorized.
  // Holds { channelId, clientId, token, userId, ... }.
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

  function sendRouteMessage(route) {
    if (!auth) {
      return Promise.reject(new Error('Not authorized'));
    }
    return fetch(EBS_BASE_URL + '/routes/' + encodeURIComponent(route.id) + '/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + auth.token
      }
    }).then(function (res) {
      return res.json().then(function (body) {
        if (!res.ok) {
          throw new Error(body.detail || ('EBS responded ' + res.status));
        }
        return body;
      });
    });
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
        showToast(err.message);
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
