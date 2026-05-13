// GodWeb · Xianxia FX (Enhanced)
// Drives runtime effects on top of xianxia-fx.css:
//   1. starfield canvas (Thiên Địa Linh Khí) with spirit purple & cinnabar stars
//   2. logo hover particle burst (Linh Lực) with violet particles
//   3. global click shockwave (Chấn Động Linh Lực)
//
// All effects auto-disable when the user prefers reduced motion. The script
// is defensive: if any selector is missing the rest of the page still works.

(function () {
    'use strict';

    var prefersReducedMotion = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ────────────────────────────────────────────────────────────
    // 1. Starfield canvas
    // ────────────────────────────────────────────────────────────
    function initStarfield() {
        if (prefersReducedMotion) return;
        var canvas = document.querySelector('canvas.xx-stars-canvas');
        if (!canvas) return;
        var ctx = canvas.getContext('2d');
        if (!ctx) return;

        var dpr = Math.min(window.devicePixelRatio || 1, 2);
        var stars = [];
        var bokehs = [];                              // larger, blurred depth-of-field particles
        var STAR_COUNT_BASE = 80;
        var BOKEH_COUNT_BASE = 10;
        var w = 0, h = 0;
        // Pointer-driven parallax target; smoothed in the render loop.
        var pxTarget = 0, pyTarget = 0;
        var px = 0, py = 0;
        var PARALLAX_MAX = 8;

        function resize() {
            w = window.innerWidth;
            h = window.innerHeight;
            canvas.width  = Math.floor(w * dpr);
            canvas.height = Math.floor(h * dpr);
            canvas.style.width  = w + 'px';
            canvas.style.height = h + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }

        function seed() {
            stars = [];
            bokehs = [];
            // Scale star count gently with viewport area, capped to keep mobile cheap.
            var density = Math.min(1.6, Math.max(0.6, (w * h) / (1280 * 720)));
            var count = Math.floor(STAR_COUNT_BASE * density);
            for (var i = 0; i < count; i++) {
                stars.push({
                    x:  Math.random() * w,
                    y:  Math.random() * h,
                    z:  0.4 + Math.random() * 1.8,        // depth, controls size + speed + parallax weight
                    vx: (Math.random() - 0.5) * 0.035,
                    vy: -0.04 - Math.random() * 0.05,     // gentle upward drift
                    tw: Math.random() * Math.PI * 2,      // twinkle phase
                    tws: 0.008 + Math.random() * 0.012,   // per-star twinkle speed
                    hue: Math.random() < 0.20 ? 'cyan' : Math.random() < 0.08 ? 'violet' : Math.random() < 0.04 ? 'cinnabar' : 'gold'
                });
            }
            // Bokeh particles: large, blurred, slow — give the page a real
            // depth-of-field feel like the user's luxury reference image.
            var bcount = Math.floor(BOKEH_COUNT_BASE * density);
            for (var j = 0; j < bcount; j++) {
                bokehs.push({
                    x:  Math.random() * w,
                    y:  Math.random() * h,
                    r:  22 + Math.random() * 46,           // 22 – 68 px radius
                    a:  0.04 + Math.random() * 0.10,       // very subtle alpha
                    vx: (Math.random() - 0.5) * 0.022,
                    vy: -0.018 - Math.random() * 0.030,    // drift up slowly
                    tw: Math.random() * Math.PI * 2,
                    tws: 0.004 + Math.random() * 0.008,
                    hue: Math.random() < 0.30 ? 'cyan' : Math.random() < 0.15 ? 'violet' : 'gold'
                });
            }
        }

        function drawStar(s, twinkle) {
            var radius = s.z * 1.05;
            var alpha  = Math.min(1, twinkle * (s.z / 2));
            var rgb = s.hue === 'cyan' ? '127, 220, 255' : s.hue === 'violet' ? '167, 139, 250' : s.hue === 'cinnabar' ? '248, 113, 113' : '255, 215, 0';
            // Simple circle with glow — much cheaper than radialGradient per star
            ctx.globalAlpha = alpha * 0.3;
            ctx.fillStyle = 'rgb(' + rgb + ')';
            ctx.beginPath();
            ctx.arc(s.x, s.y, radius * 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = alpha * 0.85;
            ctx.fillStyle = 'rgba(255, 247, 220, 1)';
            ctx.beginPath();
            ctx.arc(s.x, s.y, Math.max(0.5, radius * 0.55), 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1;
        }

        function drawBokeh(b, twinkle) {
            var alpha = b.a * (0.7 + 0.3 * twinkle);
            var rgb = b.hue === 'cyan' ? '127, 220, 255' : b.hue === 'violet' ? '167, 139, 250' : '255, 215, 0';
            ctx.globalAlpha = alpha;
            ctx.fillStyle = 'rgb(' + rgb + ')';
            ctx.beginPath();
            ctx.arc(b.x, b.y, b.r * 0.6, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1;
        }

        var lastFrame = 0;
        var TARGET_FPS = 30;
        var FRAME_INTERVAL = 1000 / TARGET_FPS;

        function tick(now) {
            requestAnimationFrame(tick);
            if (now - lastFrame < FRAME_INTERVAL) return;
            lastFrame = now;

            px += (pxTarget - px) * 0.06;
            py += (pyTarget - py) * 0.06;
            canvas.style.setProperty('--xx-px', px.toFixed(2) + 'px');
            canvas.style.setProperty('--xx-py', py.toFixed(2) + 'px');

            ctx.clearRect(0, 0, w, h);

            for (var k = 0; k < bokehs.length; k++) {
                var b = bokehs[k];
                b.x += b.vx;
                b.y += b.vy;
                b.tw += b.tws;
                if (b.y + b.r < 0) { b.y = h + b.r; b.x = Math.random() * w; }
                if (b.x + b.r < 0) b.x = w + b.r;
                if (b.x - b.r > w) b.x = -b.r;
                var btw = 0.6 + 0.4 * Math.sin(b.tw);
                drawBokeh(b, btw);
            }

            for (var i = 0; i < stars.length; i++) {
                var s = stars[i];
                s.x += s.vx;
                s.y += s.vy;
                s.tw += s.tws;
                if (s.y < -8) { s.y = h + 8; s.x = Math.random() * w; }
                if (s.x < -8) s.x = w + 8;
                if (s.x > w + 8) s.x = -8;
                var twinkle = 0.55 + 0.45 * Math.sin(s.tw);
                drawStar(s, twinkle);
            }
        }

        resize();
        seed();
        window.addEventListener('resize', function () { resize(); seed(); });

        // Parallax: subtle 8px max offset — reads as depth without nausea.
        window.addEventListener('pointermove', function (ev) {
            var nx = (ev.clientX / w - 0.5) * 2;     // -1 .. 1
            var ny = (ev.clientY / h - 0.5) * 2;
            pxTarget = -nx * PARALLAX_MAX;
            pyTarget = -ny * PARALLAX_MAX;
        }, { passive: true });

        requestAnimationFrame(tick);
    }

    // ────────────────────────────────────────────────────────────
    // 2. Logo hover particle burst
    // ────────────────────────────────────────────────────────────
    function initLogoParticles() {
        if (prefersReducedMotion) return;
        var logos = document.querySelectorAll('.xx-logo');
        if (!logos.length) return;

        logos.forEach(function (logo) {
            var layer = logo.querySelector('.xx-particles');
            if (!layer) {
                layer = document.createElement('span');
                layer.className = 'xx-particles';
                logo.appendChild(layer);
            }

            var emitterId = null;

            function emit() {
                // 2-3 particles per tick keeps things smooth.
                var count = 2 + Math.floor(Math.random() * 2);
                for (var i = 0; i < count; i++) {
                    var p = document.createElement('span');
                    var rnd = Math.random();
                    var particleClass = rnd < 0.25 ? ' xx-particle-cyan' : rnd < 0.35 ? ' xx-particle-violet' : '';
                    p.className = 'xx-particle' + particleClass;
                    var angle = Math.random() * Math.PI * 2;
                    var dist  = 38 + Math.random() * 36;
                    p.style.setProperty('--xx-dx', Math.cos(angle) * dist + 'px');
                    p.style.setProperty('--xx-dy', Math.sin(angle) * dist + 'px');
                    layer.appendChild(p);
                    // Self-clean to keep the DOM lean.
                    p.addEventListener('animationend', function (ev) {
                        if (ev.target && ev.target.parentNode === layer) {
                            layer.removeChild(ev.target);
                        }
                    });
                }
            }

            logo.addEventListener('mouseenter', function () {
                if (emitterId !== null) return;
                emit();                                 // immediate first wave
                // Slightly slower cadence — looks more deliberate, less spammy.
                emitterId = window.setInterval(emit, 180);
            });
            logo.addEventListener('mouseleave', function () {
                if (emitterId !== null) {
                    window.clearInterval(emitterId);
                    emitterId = null;
                }
            });
        });
    }

    // ────────────────────────────────────────────────────────────
    // 3. Click shockwave
    //
    // The wave is appended to a single body-level layer rather than the
    // clicked host. Two reasons:
    //   1. host click handlers sometimes replace their own innerHTML
    //      (e.g. icon swap on a theme-toggle button), which would wipe a
    //      child wave element before its animation could even start.
    //   2. dropdowns / cards with overflow:hidden would otherwise clip
    //      the wave to a tiny visible portion.
    // ────────────────────────────────────────────────────────────
    var shockwaveLayer = null;

    function ensureShockwaveLayer() {
        if (shockwaveLayer && document.body.contains(shockwaveLayer)) {
            return shockwaveLayer;
        }
        shockwaveLayer = document.createElement('div');
        shockwaveLayer.className = 'xx-shockwave-layer';
        shockwaveLayer.setAttribute('aria-hidden', 'true');
        document.body.appendChild(shockwaveLayer);
        return shockwaveLayer;
    }

    function initShockwave() {
        if (prefersReducedMotion) return;

        ensureShockwaveLayer();

        // Selectors that should "absorb" linh khí on click.
        var targetSelectors = [
            '.btn',
            'button:not(.btn-no-shockwave)',
            '.card',
            '.product-card',
            '.post-card',
            '.dashboard-card',
            '.notification-toggle',
            '.theme-toggle-btn'
        ].join(',');

        document.addEventListener('click', function (ev) {
            var host = ev.target.closest(targetSelectors);
            if (!host) return;
            spawnShockwave(ev);
        }, true);
    }

    function spawnShockwave(ev) {
        var layer = ensureShockwaveLayer();
        var x = ev.clientX, y = ev.clientY;

        // Primary ring — bright gold/cyan rim, ~820ms.
        var primary = document.createElement('span');
        primary.className = 'xx-shockwave';
        primary.style.setProperty('--xx-x', x + 'px');
        primary.style.setProperty('--xx-y', y + 'px');
        layer.appendChild(primary);
        primary.addEventListener('animationend', function () {
            if (primary.parentNode === layer) layer.removeChild(primary);
        });

        // Echo ring — slimmer cyan/violet, spawned 120ms later. Gives the
        // "linh khí" ripple double-pulse feel instead of a single flash.
        window.setTimeout(function () {
            var echo = document.createElement('span');
            echo.className = 'xx-shockwave xx-shockwave-echo';
            echo.style.setProperty('--xx-x', x + 'px');
            echo.style.setProperty('--xx-y', y + 'px');
            layer.appendChild(echo);
            echo.addEventListener('animationend', function () {
                if (echo.parentNode === layer) layer.removeChild(echo);
            });
        }, 120);
    }

    // ────────────────────────────────────────────────────────────
    // Boot
    // ────────────────────────────────────────────────────────────
    function boot() {
        try { initStarfield(); }      catch (e) { /* non-fatal */ }
        try { initLogoParticles(); }  catch (e) { /* non-fatal */ }
        try { initShockwave(); }      catch (e) { /* non-fatal */ }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
