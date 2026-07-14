/*
 * Route definitions shared by overlay + config pages. Ids must match
 * ../../ebs/app/routes_config.py.
 *
 * TEMPORARY: forward/backward drive-pulse test in place of preset routes —
 * see routes_config.py for why.
 */
window.ROBOT_ROUTES = [
  { id: 'forward', name: 'Forward', description: 'Move forward briefly', icon: '⬆' },
  { id: 'backward', name: 'Backward', description: 'Move backward briefly', icon: '⬇' },
  { id: 'auto-start', name: 'Start Auto Mode', description: 'Engage autonomous driving', icon: '▶' },
  { id: 'auto-stop', name: 'Stop Auto Mode', description: 'Disengage autonomous driving', icon: '■' }
];
