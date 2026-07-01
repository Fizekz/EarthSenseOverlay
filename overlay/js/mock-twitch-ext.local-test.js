/*
 * DRY-TEST ONLY. Not part of the real extension — stands in for the real
 * Twitch Extension Helper (twitch-ext.min.js) so overlay.js's
 * Twitch.ext.onAuthorized() call fires locally, the same way it would once
 * this is actually running inside a Twitch-hosted iframe.
 *
 * Do not ship this file or reference it from the real overlay.html.
 */
(function () {
  'use strict';
  window.Twitch = {
    ext: {
      onAuthorized: function (cb) {
        setTimeout(function () {
          cb({ token: 'dry-test-token', userId: 'U000', channelId: 'C000', clientId: 'dry-test' });
        }, 200);
      }
    }
  };
})();
