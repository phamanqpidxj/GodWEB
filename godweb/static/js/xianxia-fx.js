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
    // ────────────────────────────────────────────────────────────
    function initShockwave() {
        if (prefersReducedMotion) return;

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
            // Skip submit buttons that immediately navigate away — animation
            // would be cut off mid-flight and looks jarring.
            if (host.tagName === 'BUTTON' && host.getAttribute('type') === 'submit') {
                // Still emit; modern browsers paint the next frame before nav.
            }
            spawnShockwave(host, ev);
        }, true);
    }

    function spawnShockwave(host, ev) {
        // Need positioning context + clipping for the ring.
        var prevPosition = host.style.position;
        var prevOverflow = host.style.overflow;
        if (getComputedStyle(host).position === 'static') {
            host.style.position = 'relative';
        }
        // We only force overflow:hidden if the host doesn't already define one;
        // otherwise we'd clobber dropdowns / popovers anchored to the same node.
        if (!host.classList.contains('dropdown')) {
            host.classList.add('xx-shockwave-host');
        }

        var rect = host.getBoundingClientRect();
        var x = ev.clientX - rect.left;
        var y = ev.clientY - rect.top;

        var wave = document.createElement('span');
        wave.className = 'xx-shockwave';
        wave.style.setProperty('--xx-x', x + 'px');
        wave.style.setProperty('--xx-y', y + 'px');
        host.appendChild(wave);

        wave.addEventListener('animationend', function () {
            if (wave.parentNode === host) host.removeChild(wave);
            // Restore inline styles we may have set so we don't leak state.
            if (!prevPosition) host.style.position = prevPosition;
            if (!prevOverflow) host.style.overflow = prevOverflow;
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
