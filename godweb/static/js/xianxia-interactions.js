// GodWeb - Xianxia Interaction Effects
// Ink splash clicks, qi ripples, cursor trail, rune hover effects.
// All effects auto-disable when the user prefers reduced motion.

(function () {
    'use strict';

    var prefersReducedMotion = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ────────────────────────────────────────────────────────────
    // 1. Ink Splash Click Effect
    // ────────────────────────────────────────────────────────────
    var inkLayer = null;

    function ensureInkLayer() {
        if (inkLayer && document.body.contains(inkLayer)) return inkLayer;
        inkLayer = document.createElement('div');
        inkLayer.className = 'xx-ink-splash-layer';
        inkLayer.setAttribute('aria-hidden', 'true');
        document.body.appendChild(inkLayer);
        return inkLayer;
    }

    function initInkSplash() {
        if (prefersReducedMotion) return;
        ensureInkLayer();

        document.addEventListener('click', function (ev) {
            var layer = ensureInkLayer();
            var x = ev.clientX;
            var y = ev.clientY;

            // Main ink splash
            var splash = document.createElement('span');
            splash.className = 'xx-ink-splash';
            splash.style.left = x + 'px';
            splash.style.top = y + 'px';
            layer.appendChild(splash);
            splash.addEventListener('animationend', function () {
                if (splash.parentNode === layer) layer.removeChild(splash);
            });

            // Scatter 4-6 ink droplets
            var dropletCount = 4 + Math.floor(Math.random() * 3);
            for (var i = 0; i < dropletCount; i++) {
                var droplet = document.createElement('span');
                droplet.className = 'xx-ink-droplet';
                var angle = Math.random() * Math.PI * 2;
                var dist = 15 + Math.random() * 35;
                droplet.style.left = x + 'px';
                droplet.style.top = y + 'px';
                droplet.style.setProperty('--xx-drop-x', (Math.cos(angle) * dist) + 'px');
                droplet.style.setProperty('--xx-drop-y', (Math.sin(angle) * dist) + 'px');

                // Vary droplet color
                if (Math.random() < 0.3) {
                    droplet.style.background = 'rgba(251, 191, 36, 0.5)';
                } else if (Math.random() < 0.15) {
                    droplet.style.background = 'rgba(167, 139, 250, 0.4)';
                }

                layer.appendChild(droplet);
                droplet.addEventListener('animationend', function () {
                    if (this.parentNode === layer) layer.removeChild(this);
                });
            }
        });
    }

    // ────────────────────────────────────────────────────────────
    // 2. Spiritual Cursor Trail
    // ────────────────────────────────────────────────────────────
    var trailThrottle = 0;

    function initCursorTrail() {
        if (prefersReducedMotion) return;
        if (window.innerWidth < 768) return; // Skip on mobile

        document.addEventListener('mousemove', function (ev) {
            var now = Date.now();
            if (now - trailThrottle < 50) return; // Throttle to ~20fps
            trailThrottle = now;

            var dot = document.createElement('span');
            dot.className = 'xx-cursor-trail';
            dot.style.left = ev.clientX + 'px';
            dot.style.top = ev.clientY + 'px';

            // Random color variation
            if (Math.random() < 0.2) {
                dot.style.background = 'radial-gradient(circle, rgba(251, 191, 36, 0.4) 0%, rgba(251, 191, 36, 0.1) 50%, transparent 100%)';
            } else if (Math.random() < 0.1) {
                dot.style.background = 'radial-gradient(circle, rgba(167, 139, 250, 0.3) 0%, rgba(167, 139, 250, 0.08) 50%, transparent 100%)';
            }

            document.body.appendChild(dot);
            dot.addEventListener('animationend', function () {
                if (dot.parentNode) dot.parentNode.removeChild(dot);
            });
        }, { passive: true });
    }

    // ────────────────────────────────────────────────────────────
    // 3. Qi Flow Lines
    // ────────────────────────────────────────────────────────────
    function initQiFlow() {
        if (prefersReducedMotion) return;

        var container = document.createElement('div');
        container.className = 'xx-qi-flow';
        container.setAttribute('aria-hidden', 'true');
        container.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:-1;';
        document.body.appendChild(container);

        var lineCount = 3;
        for (var i = 0; i < lineCount; i++) {
            createQiLine(container, i);
        }
    }

    function createQiLine(container, index) {
        var line = document.createElement('div');
        line.className = 'xx-qi-line';
        var top = 15 + (index * 30) + (Math.random() * 15);
        var duration = 12 + Math.random() * 8;
        var delay = index * 3 + Math.random() * 4;
        var width = 200 + Math.random() * 300;

        line.style.top = top + '%';
        line.style.width = width + 'px';
        line.style.setProperty('--xx-qi-duration', duration + 's');
        line.style.animationDelay = delay + 's';

        container.appendChild(line);

        // Restart animation when it ends
        line.addEventListener('animationiteration', function () {
            line.style.top = (15 + Math.random() * 65) + '%';
        });
    }

    // ────────────────────────────────────────────────────────────
    // 4. Enhanced Button Energy Burst on Click
    // ────────────────────────────────────────────────────────────
    function initEnergyBurst() {
        if (prefersReducedMotion) return;

        var btnSelectors = '.btn-primary, .btn-secondary, .xx-bloom';

        document.addEventListener('click', function (ev) {
            var btn = ev.target.closest(btnSelectors);
            if (!btn) return;

            var rect = btn.getBoundingClientRect();
            var x = ev.clientX - rect.left;
            var y = ev.clientY - rect.top;

            var burst = document.createElement('span');
            burst.className = 'xx-energy-burst';
            burst.style.left = x + 'px';
            burst.style.top = y + 'px';
            btn.appendChild(burst);

            burst.addEventListener('animationend', function () {
                if (burst.parentNode === btn) btn.removeChild(burst);
            });
        }, true);
    }

    // ────────────────────────────────────────────────────────────
    // Boot
    // ────────────────────────────────────────────────────────────
    function boot() {
        try { initInkSplash(); }     catch (e) { /* non-fatal */ }
        try { initCursorTrail(); }   catch (e) { /* non-fatal */ }
        try { initQiFlow(); }        catch (e) { /* non-fatal */ }
        try { initEnergyBurst(); }   catch (e) { /* non-fatal */ }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
