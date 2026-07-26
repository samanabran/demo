/**
 * SGC Shader Background - WebGL gold-metallic line animation on dark navy.
 * Replaces the retired #sgc-floating-paths (SVG/CSS) background.
 *
 * Ships disabled by default (--sgc-shader-enabled: 0 in 05_shader_bg.css).
 * Kill switch + tuning are CSS custom properties, overridable from
 * Website -> Custom CSS with no SSH access and no redeploy.
 */
(function () {
  'use strict';

  var ID = 'sgc-shader-bg';
  var VS_SOURCE = 'attribute vec2 aPos;\n' +
    'void main() {\n' +
    '  gl_Position = vec4(aPos, 0.0, 1.0);\n' +
    '}\n';

  function buildFragmentSource(linesPerGroup) {
    return [
      'precision highp float;',
      'uniform vec2 iResolution;',
      'uniform float iTime;',
      'uniform float uSpeed;',
      'uniform float uGain;',
      'uniform vec3 uGoldCore;',
      'uniform vec3 uBgTop;',
      'uniform vec3 uBgDeep;',
      '',
      'const float gridSmoothWidth = 0.015;',
      'const float scale = 5.0;',
      'const float minLineWidth = 0.01;',
      'const float maxLineWidth = 0.2;',
      'const float lineAmplitude = 1.0;',
      'const float lineFrequency = 0.2;',
      'const float warpFrequency = 0.5;',
      'const float warpAmplitude = 1.0;',
      'const float offsetFrequency = 0.5;',
      'const float minOffsetSpread = 0.6;',
      'const float maxOffsetSpread = 2.0;',
      'const int linesPerGroup = ' + linesPerGroup + ';',
      '',
      '#define drawCircle(pos, radius, coord) smoothstep(radius + gridSmoothWidth, radius, length(coord - (pos)))',
      '#define drawSmoothLine(pos, halfWidth, t) smoothstep(halfWidth, 0.0, abs(pos - (t)))',
      '#define drawCrispLine(pos, halfWidth, t) smoothstep(halfWidth + gridSmoothWidth, halfWidth, abs(pos - (t)))',
      '',
      'float random(float t) {',
      '  return (cos(t) + cos(t * 1.3 + 1.3) + cos(t * 1.4 + 1.4)) / 3.0;',
      '}',
      '',
      'float getPlasmaY(float x, float horizontalFade, float offset, float lineSpeed) {',
      '  return random(x * lineFrequency + iTime * lineSpeed) * horizontalFade * lineAmplitude + offset;',
      '}',
      '',
      'void main() {',
      '  vec2 fragCoord = gl_FragCoord.xy;',
      '  vec2 uv = fragCoord.xy / iResolution.xy;',
      '  vec2 space = (fragCoord - iResolution.xy / 2.0) / iResolution.x * 2.0 * scale;',
      '',
      '  float lineSpeed = 1.0 * uSpeed;',
      '  float warpSpeed = 0.2 * uSpeed;',
      '  float offsetSpeed = 1.33 * uSpeed;',
      '',
      '  float horizontalFade = 1.0 - (cos(uv.x * 6.28318) * 0.5 + 0.5);',
      '  float verticalFade = 1.0 - (cos(uv.y * 6.28318) * 0.5 + 0.5);',
      '',
      '  space.y += random(space.x * warpFrequency + iTime * warpSpeed) * warpAmplitude * (0.5 + horizontalFade);',
      '  space.x += random(space.y * warpFrequency + iTime * warpSpeed + 2.0) * warpAmplitude * horizontalFade;',
      '',
      '  vec3 goldCore = uGoldCore;',
      '  vec3 goldDeep = goldCore * vec3(0.45, 0.38, 0.27);',
      '  vec3 goldHot = mix(goldCore, vec3(1.0), 0.75);',
      '',
      '  vec3 lines = vec3(0.0);',
      '',
      '  for (int l = 0; l < linesPerGroup; l++) {',
      '    float normalizedLineIndex = float(l) / float(linesPerGroup);',
      '    float offsetTime = iTime * offsetSpeed;',
      '    float offsetPosition = float(l) + space.x * offsetFrequency;',
      '    float rand = random(offsetPosition + offsetTime) * 0.5 + 0.5;',
      '    float halfWidth = mix(minLineWidth, maxLineWidth, rand * horizontalFade) / 2.0;',
      '    float offset = random(offsetPosition + offsetTime * (1.0 + normalizedLineIndex)) * mix(minOffsetSpread, maxOffsetSpread, horizontalFade);',
      '    float linePosition = getPlasmaY(space.x, horizontalFade, offset, lineSpeed);',
      '',
      '    float halo = drawSmoothLine(linePosition, halfWidth, space.y) / 2.0;',
      '    float core = drawCrispLine(linePosition, halfWidth * 0.15, space.y);',
      '',
      '    float circleX = mod(float(l) + iTime * lineSpeed, 25.0) - 12.0;',
      '    vec2 circlePosition = vec2(circleX, getPlasmaY(circleX, horizontalFade, offset, lineSpeed));',
      '    float dot = drawCircle(circlePosition, 0.01, space) * 4.0;',
      '',
      '    float t = clamp(rand * (0.35 + 0.75 * horizontalFade), 0.0, 1.0);',
      '    vec3 metal = mix(goldDeep, goldCore, smoothstep(0.00, 0.55, t));',
      '    metal = mix(metal, goldHot, smoothstep(0.72, 1.00, t));',
      '',
      '    lines += (halo * goldCore * 0.55 + core * metal + dot * goldHot) * rand;',
      '  }',
      '',
      '  vec3 bg = mix(uBgDeep, uBgTop, 0.35 + 0.65 * verticalFade);',
      '  vec3 color = min(bg + lines * uGain, vec3(1.0));',
      '',
      '  gl_FragColor = vec4(color, 1.0);',
      '}'
    ].join('\n');
  }

  function init() {
    // F6 - double-init guard
    if (document.getElementById(ID) || window.__sgcShaderBg) {
      return;
    }

    // --- Scope gate: bail out before injecting anything ---

    // 1 (B4) - website builder loads the page in an iframe
    // (website.website_preview) since Odoo 16; editor_enable is stamped on
    // the iframe body after load and #oe_snippets lives in the parent
    // document, so from inside the iframe neither is visible at gate time.
    // window.top !== window.self is safe to evaluate cross-origin and
    // catches the builder, website_preview, and any embed. Note: this also
    // means an admin browsing their own site from the Odoo backend's
    // Website app preview will never see the background - same iframe,
    // same edit-mode hazard one click away. By design.
    if (window.top !== window.self) {
      return;
    }

    var root = document.documentElement;
    var rootStyle = getComputedStyle(root);

    // 2 (S2) - kill switch, overridable via Website -> Custom CSS with no
    // SSH access and no redeploy.
    if (parseFloat(rootStyle.getPropertyValue('--sgc-shader-enabled')) !== 1) {
      return;
    }

    // 3-6 - defense-in-depth for non-iframe cases.
    if (document.body.classList.contains('editor_enable') || document.querySelector('#oe_snippets')) {
      return;
    }
    if (document.querySelector('.o_portal, .o_portal_wrap')) {
      return;
    }
    if (document.querySelector('.oe_website_login, .o_login_layout')) {
      return;
    }
    if (document.body.classList.contains('o_web_client')) {
      return;
    }

    // --- Config read from CSS custom properties ---

    function cssNumber(name, fallback) {
      var v = parseFloat(rootStyle.getPropertyValue(name));
      return isFinite(v) ? v : fallback;
    }

    function clampInt(v, min, max, fallback) {
      var n = parseInt(v, 10);
      if (!isFinite(n)) {
        return fallback;
      }
      return Math.max(min, Math.min(max, n));
    }

    var gain = cssNumber('--sgc-shader-gain', 0.55);
    var speed = cssNumber('--sgc-shader-speed', 0.13);
    var linesPerGroup = clampInt(rootStyle.getPropertyValue('--sgc-shader-lines'), 4, 24, 12);

    function parseColor(str, fallback) {
      if (!str) {
        return fallback;
      }
      var m = str.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i);
      if (!m) {
        return fallback;
      }
      return [parseFloat(m[1]) / 255, parseFloat(m[2]) / 255, parseFloat(m[3]) / 255];
    }

    var GOLD_FALLBACK = [0.784, 0.635, 0.290]; // #C8A24A
    var BG_FALLBACK = [0.055, 0.106, 0.176]; // #0E1B2D

    var goldOverride = rootStyle.getPropertyValue('--sgc-bg-shader-gold');
    var goldCore = parseColor(goldOverride, null) || parseColor(getComputedStyle(document.body).color ? goldOverride : null, GOLD_FALLBACK) || GOLD_FALLBACK;

    // N1 - background is MEASURED from the resolved body backgroundColor,
    // not read from a token. The dark-mode override in
    // sgc_realestate_website/static/src/css/responsive.css sets
    // body { background-color: #1F2937 } as a literal that never touches
    // --re-bg-page, so a token read is invariant across light/dark and
    // fixes nothing. --sgc-bg-shader-top is override-only (no default).
    function measureBgTop() {
      var override = rootStyle.getPropertyValue('--sgc-bg-shader-top');
      var overridden = parseColor(override, null);
      if (overridden) {
        return overridden;
      }
      return parseColor(getComputedStyle(document.body).backgroundColor, BG_FALLBACK);
    }

    function deriveBgDeep(bgTop) {
      return [bgTop[0] * 0.43, bgTop[1] * 0.59, bgTop[2] * 0.64];
    }

    var bgTop = measureBgTop();
    var bgDeep = deriveBgDeep(bgTop);

    // --- Canvas: direct child of <body>, outside #wrapwrap ---
    // Any ancestor with transform/filter/perspective/will-change/contain/
    // isolation/opacity<1 creates a containing block that traps a fixed
    // element. GSAP ScrollTrigger sets transform on pinned scroll-hero
    // sections; staying outside #wrapwrap makes those irrelevant.

    var canvas = document.createElement('canvas');
    canvas.id = ID;
    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.backgroundColor = 'rgb(' + Math.round(bgTop[0] * 255) + ',' + Math.round(bgTop[1] * 255) + ',' + Math.round(bgTop[2] * 255) + ')';
    document.body.appendChild(canvas);

    var glOpts = {
      alpha: true, // B3 - required. With alpha:false the GL surface is
      // opaque and composites over the CSS fallback; on context loss or a
      // re-composite of an empty buffer that shows black, not navy.
      depth: false,
      stencil: false,
      antialias: false,
      preserveDrawingBuffer: false,
      powerPreference: 'low-power',
      failIfMajorPerformanceCaveat: true
    };

    var gl = canvas.getContext('webgl', glOpts) || canvas.getContext('experimental-webgl', glOpts);

    // F1 - no WebGL: remove the canvas, land on the flat CSS navy.
    if (!gl) {
      canvas.remove();
      return;
    }

    var program = null;
    var vertexShader = null;
    var fragmentShader = null;
    var buffer = null;
    var uniforms = {};
    var rafId = null;
    var lastFrameTime = 0;
    var clock = 0;
    var stopped = false;
    var destroyed = false;
    var contextLost = false;
    var restoreAttempts = 0;
    var resizeTimer = null;
    var lastW = -1;
    var lastH = -1;
    var reinitCount = 0;
    var heroObserver = null;
    var heroIntersecting = false;
    var reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    var colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');

    function compileShader(type, source) {
      var shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.warn('[sgc-shader-bg] shader compile failed: ' + gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    }

    function buildProgram() {
      vertexShader = compileShader(gl.VERTEX_SHADER, VS_SOURCE);
      fragmentShader = compileShader(gl.FRAGMENT_SHADER, buildFragmentSource(linesPerGroup));
      if (!vertexShader || !fragmentShader) {
        return false;
      }
      var prog = gl.createProgram();
      gl.attachShader(prog, vertexShader);
      gl.attachShader(prog, fragmentShader);
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
        console.warn('[sgc-shader-bg] program link failed: ' + gl.getProgramInfoLog(prog));
        gl.deleteProgram(prog);
        return false;
      }
      program = prog;
      return true;
    }

    function setupBuffer() {
      buffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    }

    function fetchUniforms() {
      uniforms.iResolution = gl.getUniformLocation(program, 'iResolution');
      uniforms.iTime = gl.getUniformLocation(program, 'iTime');
      uniforms.uSpeed = gl.getUniformLocation(program, 'uSpeed');
      uniforms.uGain = gl.getUniformLocation(program, 'uGain');
      uniforms.uGoldCore = gl.getUniformLocation(program, 'uGoldCore');
      uniforms.uBgTop = gl.getUniformLocation(program, 'uBgTop');
      uniforms.uBgDeep = gl.getUniformLocation(program, 'uBgDeep');
    }

    function applyClearColor() {
      gl.clearColor(bgTop[0], bgTop[1], bgTop[2], 1.0);
    }

    // F2 - shader compile / link failure: no program bound, remove canvas.
    if (!buildProgram()) {
      canvas.remove();
      return;
    }
    setupBuffer();
    fetchUniforms();
    applyClearColor();

    function computeRenderScale(cssW, cssH) {
      var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      var scale = dpr;
      if (cssW <= 768) {
        scale *= 0.5;
      }
      var w = cssW * scale;
      var h = cssH * scale;
      var maxPixels = 1920 * 1080;
      if (w * h > maxPixels) {
        var reduce = Math.sqrt(maxPixels / (w * h));
        scale *= reduce;
      }
      return scale;
    }

    function resize(force) {
      var cssW = window.innerWidth;
      var cssH = window.innerHeight;
      var scale = computeRenderScale(cssW, cssH);
      var w = Math.round(cssW * scale);
      var h = Math.round(cssH * scale);

      if (!force && Math.abs(h - lastH) < 120 && w === lastW) {
        // F5 - mobile URL-bar collapse/expand: skip reallocation for a
        // height-only delta under ~120px.
        return;
      }
      if (w === lastW && h === lastH) {
        return;
      }
      lastW = w;
      lastH = h;
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
      if (uniforms.iResolution) {
        gl.useProgram(program);
        gl.uniform2f(uniforms.iResolution, w, h);
      }
      reinitCount++;
    }

    function onResize() {
      if (resizeTimer) {
        clearTimeout(resizeTimer);
      }
      resizeTimer = setTimeout(function () {
        resize(false);
      }, 150);
    }

    resize(true);

    // --- Pause conditions ---

    function updateStoppedState() {
      stopped = document.hidden || heroIntersecting || (reducedMotionQuery.matches && clock > 0);
    }

    function onVisibilityChange() {
      updateStoppedState();
      if (!stopped && !rafId && !contextLost && !destroyed) {
        lastFrameTime = 0; // resume with a clamped delta, no time jump
        rafId = requestAnimationFrame(tick);
      }
    }

    function onReducedMotionChange() {
      updateStoppedState();
      if (!reducedMotionQuery.matches && !rafId && !contextLost && !destroyed) {
        lastFrameTime = 0;
        rafId = requestAnimationFrame(tick);
      }
    }

    // N1/R3 - OS dark-mode can toggle at runtime (not just on reload).
    // Re-measure and update both the uniform and the CSS fallback paint,
    // and re-apply the GL clear color so it never mismatches.
    function onColorSchemeChange() {
      bgTop = measureBgTop();
      bgDeep = deriveBgDeep(bgTop);
      canvas.style.backgroundColor = 'rgb(' + Math.round(bgTop[0] * 255) + ',' + Math.round(bgTop[1] * 255) + ',' + Math.round(bgTop[2] * 255) + ')';
      if (!contextLost && program) {
        gl.useProgram(program);
        applyClearColor();
      }
    }

    // Scroll-hero sections paint their own opaque full-screen canvas, so
    // the shader is invisible behind them anyway; stopping it hands the
    // GPU budget to the hero engine exactly when it needs it. Coupling is
    // a DOM selector only - never scroll-linked (scroll-linked start/stop
    // of a fullscreen animation is what reads as "flicker").
    var heroSections = document.querySelectorAll('section[data-snippet="s_re_scroll_hero"], section[data-snippet="s_re_scroll_hero_v2"]');
    if (heroSections.length && 'IntersectionObserver' in window) {
      heroObserver = new IntersectionObserver(function (entries) {
        heroIntersecting = entries.some(function (e) { return e.isIntersecting; });
        onVisibilityChange();
      });
      heroSections.forEach(function (s) { heroObserver.observe(s); });
    }

    // --- Monotonic render loop ---
    // iTime accumulates from the rAF timestamp delta, clamped, so
    // pause/resume, tab-switch, and long frames can never produce a time
    // jump (the reference's Date.now()-based clock had exactly this bug).

    function tick(now) {
      rafId = null;
      updateStoppedState();
      if (stopped || contextLost || destroyed) {
        if (reducedMotionQuery.matches && clock === 0) {
          // render exactly one static frame, then stop permanently
        } else {
          return;
        }
      }

      if (lastFrameTime === 0) {
        lastFrameTime = now;
      }
      var dt = Math.min(now - lastFrameTime, 50);
      lastFrameTime = now;

      if (now - (tick._last30 || 0) < 33 && tick._last30) {
        rafId = requestAnimationFrame(tick);
        return;
      }
      tick._last30 = now;

      clock += dt / 1000;

      gl.useProgram(program);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      var loc = gl.getAttribLocation(program, 'aPos');
      gl.enableVertexAttribArray(loc);
      gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

      if (uniforms.iTime) gl.uniform1f(uniforms.iTime, clock);
      if (uniforms.uSpeed) gl.uniform1f(uniforms.uSpeed, speed);
      if (uniforms.uGain) gl.uniform1f(uniforms.uGain, gain);
      if (uniforms.uGoldCore) gl.uniform3f(uniforms.uGoldCore, goldCore[0], goldCore[1], goldCore[2]);
      if (uniforms.uBgTop) gl.uniform3f(uniforms.uBgTop, bgTop[0], bgTop[1], bgTop[2]);
      if (uniforms.uBgDeep) gl.uniform3f(uniforms.uBgDeep, bgDeep[0], bgDeep[1], bgDeep[2]);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

      if (!stopped && !contextLost && !destroyed) {
        rafId = requestAnimationFrame(tick);
      } else if (reducedMotionQuery.matches) {
        rafId = null; // one frame rendered, stop permanently
      }
    }

    updateStoppedState();
    if (!stopped) {
      rafId = requestAnimationFrame(tick);
    } else if (reducedMotionQuery.matches) {
      // reduced motion: render exactly one frame immediately
      rafId = requestAnimationFrame(tick);
    }

    // --- Context loss / restore (F3 / F4) ---

    function onContextLost(e) {
      e.preventDefault(); // required for the context to ever be restorable
      contextLost = true;
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    }

    function onContextRestored() {
      restoreAttempts++;
      if (restoreAttempts > 2) {
        destroy();
        return;
      }
      contextLost = false;
      reinitCount++;
      if (!buildProgram()) {
        canvas.remove();
        return;
      }
      setupBuffer();
      fetchUniforms();
      applyClearColor();
      lastW = -1;
      lastH = -1;
      resize(true);
      lastFrameTime = 0;
      if (!stopped) {
        rafId = requestAnimationFrame(tick);
      }
    }

    canvas.addEventListener('webglcontextlost', onContextLost, false);
    canvas.addEventListener('webglcontextrestored', onContextRestored, false);

    window.addEventListener('resize', onResize);
    document.addEventListener('visibilitychange', onVisibilityChange);
    reducedMotionQuery.addEventListener ? reducedMotionQuery.addEventListener('change', onReducedMotionChange) : reducedMotionQuery.addListener(onReducedMotionChange);
    colorSchemeQuery.addEventListener ? colorSchemeQuery.addEventListener('change', onColorSchemeChange) : colorSchemeQuery.addListener(onColorSchemeChange);

    // F7 - destroy(): every listener registered above has a matching
    // removal here.
    function destroy() {
      if (destroyed) {
        return;
      }
      destroyed = true;
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      if (resizeTimer) {
        clearTimeout(resizeTimer);
      }
      window.removeEventListener('resize', onResize);
      document.removeEventListener('visibilitychange', onVisibilityChange);
      reducedMotionQuery.removeEventListener ? reducedMotionQuery.removeEventListener('change', onReducedMotionChange) : reducedMotionQuery.removeListener(onReducedMotionChange);
      colorSchemeQuery.removeEventListener ? colorSchemeQuery.removeEventListener('change', onColorSchemeChange) : colorSchemeQuery.removeListener(onColorSchemeChange);
      canvas.removeEventListener('webglcontextlost', onContextLost, false);
      canvas.removeEventListener('webglcontextrestored', onContextRestored, false);
      if (heroObserver) {
        heroObserver.disconnect();
      }
      var loseExt = gl.getExtension('WEBGL_lose_context');
      if (loseExt) {
        loseExt.loseContext();
      }
      if (program) {
        gl.deleteProgram(program);
      }
      if (vertexShader) {
        gl.deleteShader(vertexShader);
      }
      if (fragmentShader) {
        gl.deleteShader(fragmentShader);
      }
      if (buffer) {
        gl.deleteBuffer(buffer);
      }
      if (canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
      }
      window.__sgcShaderBg = null;
    }

    window.__sgcShaderBg = {
      destroy: destroy,
      getReinitCount: function () { return reinitCount; },
      getRestoreAttempts: function () { return restoreAttempts; }
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
