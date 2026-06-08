/*
 * Broadcaster config page. For now it's read-only: it lists the routes that
 * viewers will see so the broadcaster knows what the extension does.
 *
 * Later you can let broadcasters enable/disable routes and persist choices
 * with Twitch.ext.configuration.set(...) on the 'broadcaster' segment.
 */
(function () {
  'use strict';

  var listEl = document.getElementById('config-routes');
  var statusEl = document.getElementById('config-status');
  var routes = window.ROBOT_ROUTES || [];

  function setStatus(text, state) {
    statusEl.textContent = text;
    statusEl.setAttribute('data-state', state || 'idle');
  }

  function renderRoutes() {
    listEl.textContent = '';
    routes.forEach(function (route) {
      var li = document.createElement('li');
      li.className = 'config__item';

      var icon = document.createElement('span');
      icon.className = 'config__icon';
      icon.textContent = route.icon || '▶';

      var name = document.createElement('span');
      name.className = 'config__name';
      name.textContent = route.name;

      var desc = document.createElement('span');
      desc.className = 'config__desc';
      desc.textContent = route.description || '';

      li.appendChild(icon);
      li.appendChild(name);
      li.appendChild(desc);
      listEl.appendChild(li);
    });
  }

  renderRoutes();

  if (window.Twitch && window.Twitch.ext) {
    window.Twitch.ext.onAuthorized(function () {
      setStatus(routes.length + ' route(s) configured. You’re all set.', 'ok');
    });
  } else {
    setStatus('Local preview — ' + routes.length + ' route(s) configured.', 'warn');
  }
})();
