/**
 * SGC Floating Paths Background
 * Generates 36 animated SVG bezier paths — premium gold on dark navy.
 * Adapted from React/Framer Motion → vanilla JS for Odoo compatibility.
 *
 * Paths animate via CSS @keyframes (stroke-dashoffset + opacity).
 * JS only handles: creation, positioning, and randomized timing.
 */
(function () {
  'use strict';

  var POSITION = 1; // mirror factor (1 = default, -1 = flipped)
  var PATH_COUNT = 36;
  var SVG_NS = 'http://www.w3.org/2000/svg';
  var GOLD = [200, 162, 74]; // #C8A24A

  function init() {
    // Avoid double-injection
    if (document.getElementById('sgc-floating-paths')) return;

    var container = document.createElement('div');
    container.id = 'sgc-floating-paths';
    container.setAttribute('aria-hidden', 'true');

    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 696 316');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');

    for (var i = 0; i < PATH_COUNT; i++) {
      // Reproduce the React path generation
      var x1 = -380 - i * 5 * POSITION;
      var y1 = -189 + i * 6;
      var x2 = -312 - i * 5 * POSITION;
      var y2 = 216 - i * 6;
      var x3 = 152 - i * 5 * POSITION;
      var y3 = 343 - i * 6;
      var x4 = 616 - i * 5 * POSITION;
      var y4 = 470 - i * 6;
      var x5 = 684 - i * 5 * POSITION;
      var y5 = 875 - i * 6;

      var d = 'M' + x1 + ' ' + y1 +
              'C' + x1 + ' ' + y1 + ' ' + x2 + ' ' + y2 + ' ' + x3 + ' ' + y3 +
              'C' + x4 + ' ' + y4 + ' ' + x5 + ' ' + y5 + ' ' + x5 + ' ' + y5;

      var opacity = 0.1 + i * 0.03;
      var width = 0.5 + i * 0.03;
      var duration = 20 + Math.random() * 10; // 20-30s

      var path = document.createElementNS(SVG_NS, 'path');
      path.setAttribute('d', d);
      path.setAttribute('stroke', 'rgba(' + GOLD[0] + ',' + GOLD[1] + ',' + GOLD[2] + ',' + opacity + ')');
      path.setAttribute('stroke-width', String(width));
      path.setAttribute('opacity', String(opacity));

      // CSS custom properties for animation timing
      path.style.setProperty('--sgc-path-duration', duration.toFixed(1) + 's');
      path.style.setProperty('--sgc-path-delay', (Math.random() * -20).toFixed(1) + 's');

      svg.appendChild(path);
    }

    container.appendChild(svg);

    // Insert as first child of body — behind everything (z-index: 0)
    document.body.insertBefore(container, document.body.firstChild);
  }

  // Run when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
