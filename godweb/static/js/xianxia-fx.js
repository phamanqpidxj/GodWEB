// GodWeb · Xianxia FX
// Drives three runtime effects on top of xianxia-fx.css:
//   1. starfield canvas (Thiên Địa Linh Khí)
//   2. logo hover particle burst (Linh Lực)
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
        var STAR_COUNT_BASE = 110;
        var w = 0, h = 0;

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
            // Scale star count gently with viewport area, capped to keep mobile cheap.
            var density = Math.min(1.6, Math.max(0.6, (w * h) / (1280 * 720)));
            var count = Math.floor(STAR_COUNT_BASE * density);
            for (var i = 0; i < count; i++) {
                stars.push({
                    x:  Math.random() * w,
                    y:  Math.random() * h,
                    z:  0.4 + Math.random() * 1.6,        // depth, controls size + speed
                    vx: (Math.random() - 0.5) * 0.04,
                    vy: -0.05 - Math.random() * 0.05,     // gentle upward drift
                    tw: Math.random() * Math.PI * 2,      // twinkle phase
                    hue: Math.random() < 0.18 ? 'cyan' : 'gold'
                });
            }
        }

        function tick(t) {
            ctx.clearRect(0, 0, w, h);

            for (var i = 0; i < stars.length; i++) {
                var s = stars[i];
                s.x += s.vx;
                s.y += s.vy;
                s.tw += 0.012;

                // Wrap toroidally so stars never disappear permanently.
                if (s.y < -4) { s.y = h + 4; s.x = Math.random() * w; }
                if (s.x < -4) s.x = w + 4;
                if (s.x > w + 4) s.x = -4;

                var twinkle = 0.55 + 0.45 * Math.sin(s.tw);
                var radius  = s.z * 0.9;
                var alpha   = Math.min(1, twinkle * (s.z / 2));

                if (s.hue === 'cyan') {
                    ctx.fillStyle = 'rgba(127, 220, 255, ' + alpha.toFixed(3) + ')';
                } else {
                    ctx.fillStyle = 'rgba(255, 215, 0, ' + (alpha * 0.85).toFixed(3) + ')';
                }
                ctx.beginPath();
                ctx.arc(s.x, s.y, radius, 0, Math.PI * 2);
                ctx.fill();

                // Occasional brighter "linh khí" glow on the larger stars.
                if (s.z > 1.4) {
                    ctx.fillStyle = 'rgba(255, 255, 255, ' + (alpha * 0.25).toFixed(3) + ')';
                    ctx.beginPath();
                    ctx.arc(s.x, s.y, radius * 2.4, 0, Math.PI * 2);
                    ctx.fill();
                }
            }

            requestAnimationFrame(tick);
        }

        resize();
        seed();
        window.addEventListener('resize', function () { resize(); seed(); });
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
                    p.className = 'xx-particle' + (Math.random() < 0.25 ? ' xx-particle-cyan' : '');
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
                emitterId = window.setInterval(emit, 140);
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
        var wave = document.createElement('span');
        wave.className = 'xx-shockwave';
        wave.style.setProperty('--xx-x', ev.clientX + 'px');
        wave.style.setProperty('--xx-y', ev.clientY + 'px');
        layer.appendChild(wave);
        wave.addEventListener('animationend', function () {
            if (wave.parentNode === layer) layer.removeChild(wave);
        });
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
