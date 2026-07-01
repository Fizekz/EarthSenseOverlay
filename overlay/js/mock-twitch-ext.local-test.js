/*
 * DRY-TEST ONLY. Stands in for the real Twitch Extension Helper so
 * overlay.js's onAuthorized() fires locally. Never ship or reference
 * from the real overlay.html.
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
