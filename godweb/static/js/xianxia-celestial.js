// GodWeb - Xianxia Celestial: Advanced Motion Effects (Enhanced)
// Cherry blossom particles, floating swords/clouds/runes, GSAP scroll animations,
// parallax, spiritual vibration, mist page transitions, bloom effects.
// All effects auto-disable when the user prefers reduced motion.

(function () {
    'use strict';

    var prefersReducedMotion = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ────────────────────────────────────────────────────────────
    // 1. Cherry Blossom Particle System (Enhanced)
    // ────────────────────────────────────────────────────────────
    function initCherryBlossoms() {
        if (prefersReducedMotion) return;

        var canvas = document.getElementById('xx-petals-canvas');
        if (!canvas) return;
        var ctx = canvas.getContext('2d');
        if (!ctx) return;

        var dpr = Math.min(window.devicePixelRatio || 1, 2);
        var w = 0, h = 0;
        var petals = [];
        var PETAL_COUNT = 35;
        // Enhanced color palette with more variety
        var colors = [
            '#ffb7c5', '#ffc8d6', '#ffd4e0',
            '#e8b4b8', '#f5c6aa', '#ffe0b2'
        ];
        var time = 0;
        var animId = null;
        var running = true;

        function resize() {
            w = window.innerWidth;
            h = window.innerHeight;
            canvas.width = Math.floor(w * dpr);
            canvas.height = Math.floor(h * dpr);
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        }

        function createPetal(startAbove) {
            var type = Math.random();
            return {
                x: Math.random() * w,
                y: startAbove ? -(Math.random() * h * 0.3) : Math.random() * h,
                size: type < 0.3 ? 4 + Math.random() * 6 : 8 + Math.random() * 12,
                speedY: 0.2 + Math.random() * 0.4,
                speedX: (Math.random() - 0.5) * 0.3,
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed: (Math.random() - 0.5) * 0.025,
                oscillationFreq: 0.5 + Math.random() * 1.5,
                oscillationAmp: 15 + Math.random() * 30,
                phase: Math.random() * Math.PI * 2,
                color: colors[Math.floor(Math.random() * colors.length)],
                opacity: 0.3 + Math.random() * 0.4,
                type: type < 0.15 ? 'circle' : 'petal' // Some round particles
            };
        }

        function seed() {
            petals = [];
            for (var i = 0; i < PETAL_COUNT; i++) {
                petals.push(createPetal(false));
            }
        }

        function drawPetal(p) {
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.rotation);
            ctx.globalAlpha = p.opacity;
            ctx.fillStyle = p.color;

            if (p.type === 'circle') {
                // Small glowing dot
                ctx.beginPath();
                ctx.arc(0, 0, p.size * 0.25, 0, Math.PI * 2);
                ctx.fill();
                ctx.globalAlpha = p.opacity * 0.3;
                ctx.beginPath();
                ctx.arc(0, 0, p.size * 0.5, 0, Math.PI * 2);
                ctx.fill();
            } else {
                // Petal shape
                ctx.beginPath();
                ctx.ellipse(0, 0, p.size * 0.5, p.size * 0.25, 0, 0, Math.PI * 2);
                ctx.fill();
                // Subtle inner highlight
                ctx.globalAlpha = p.opacity * 0.4;
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.ellipse(-p.size * 0.1, -p.size * 0.05, p.size * 0.15, p.size * 0.08, 0, 0, Math.PI * 2);
                ctx.fill();
            }
            ctx.restore();
        }

        function tick() {
            if (!running) return;
            time += 0.016;
            ctx.clearRect(0, 0, w, h);

            for (var i = 0; i < petals.length; i++) {
                var p = petals[i];
                p.y += p.speedY;
                p.x += p.speedX + Math.sin(time * p.oscillationFreq + p.phase) * 0.5;
                p.rotation += p.rotationSpeed;

                if (p.y > h + p.size) {
                    petals[i] = createPetal(true);
                }
                if (p.x > w + p.size) p.x = -p.size;
                if (p.x < -p.size) p.x = w + p.size;

                drawPetal(p);
            }

            animId = requestAnimationFrame(tick);
        }

        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                running = false;
                if (animId) {
                    cancelAnimationFrame(animId);
                    animId = null;
                }
            } else {
                running = true;
                animId = requestAnimationFrame(tick);
            }
        });

        resize();
        seed();
        window.addEventListener('resize', function () { resize(); });
        animId = requestAnimationFrame(tick);
    }

    // ────────────────────────────────────────────────────────────
    // 2. Floating Swords, Clouds and Ancient Runes
    // ────────────────────────────────────────────────────────────
    function initFloatingElements() {
        if (prefersReducedMotion) return;
        if (typeof gsap === 'undefined') return;

        var container = document.getElementById('xxFloatingLayer');
        if (!container) return;

        // Create floating swords with light trails
        var swordCount = 5;
        for (var i = 0; i < swordCount; i++) {
            var sword = document.createElement('div');
            sword.className = 'xx-floating-sword';
            sword.style.top = (10 + Math.random() * 70) + '%';
            sword.style.left = (5 + Math.random() * 80) + '%';
            sword.style.width = (35 + Math.random() * 45) + 'px';
            container.appendChild(sword);

            gsap.to(sword, {
                x: (Math.random() - 0.5) * 250,
                y: (Math.random() - 0.5) * 100,
                rotation: (Math.random() - 0.5) * 25,
                duration: 25 + Math.random() * 25,
                repeat: -1,
                yoyo: true,
                ease: 'sine.inOut'
            });
        }

        // Create floating clouds
        var cloudCount = 6;
        var cloudColors = [
            'rgba(45, 212, 160, 0.12)',
            'rgba(255, 255, 255, 0.06)',
            'rgba(45, 212, 160, 0.08)',
            'rgba(251, 191, 36, 0.05)',
            'rgba(167, 139, 250, 0.04)',
            'rgba(255, 255, 255, 0.05)'
        ];

        for (var j = 0; j < cloudCount; j++) {
            var cloud = document.createElement('div');
            cloud.className = 'xx-floating-cloud';
            cloud.style.top = (8 + Math.random() * 75) + '%';
            cloud.style.left = (Math.random() * 90) + '%';
            var size = 80 + Math.random() * 180;
            cloud.style.width = size + 'px';
            cloud.style.height = (size * 0.4) + 'px';
            cloud.style.background = cloudColors[j % cloudColors.length];
            container.appendChild(cloud);

            gsap.to(cloud, {
                x: (Math.random() - 0.5) * 350,
                y: (Math.random() - 0.5) * 60,
                duration: 18 + Math.random() * 30,
                repeat: -1,
                yoyo: true,
                ease: 'sine.inOut'
            });
        }

        // Create floating rune circles
        var runeCount = 3;
        for (var k = 0; k < runeCount; k++) {
            var rune = document.createElement('div');
            rune.className = 'xx-floating-rune';
            rune.style.top = (20 + Math.random() * 50) + '%';
            rune.style.left = (10 + Math.random() * 70) + '%';
            var runeSize = 50 + Math.random() * 60;
            rune.style.width = runeSize + 'px';
            rune.style.height = runeSize + 'px';
            rune.style.animationDuration = (20 + Math.random() * 20) + 's';
            container.appendChild(rune);

            gsap.to(rune, {
                x: (Math.random() - 0.5) * 120,
                y: (Math.random() - 0.5) * 80,
                duration: 25 + Math.random() * 20,
                repeat: -1,
                yoyo: true,
                ease: 'sine.inOut'
            });
        }
    }

    // ────────────────────────────────────────────────────────────
    // 3. Scroll-Triggered Materializing Animations
    // ────────────────────────────────────────────────────────────
    function initScrollAnimations() {
        if (prefersReducedMotion) return;
        if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

        gsap.registerPlugin(ScrollTrigger);

        var targets = document.querySelectorAll(
            '.card, .feature-card, .section-title, .stat-card, .hero-content, .product-card, .post-card, .dashboard-card'
        );

        if (!targets.length) return;

        targets.forEach(function (el) {
            el.classList.remove('reveal');
        });

        gsap.set(targets, {
            opacity: 0,
            y: 40,
            filter: 'blur(6px)'
        });

        // Fallback
        setTimeout(function () {
            targets.forEach(function (el) {
                if (getComputedStyle(el).opacity === '0') {
                    el.style.opacity = '1';
                    el.style.filter = 'none';
                    el.style.transform = 'none';
                }
            });
        }, 3000);

        // Grid items with stagger
        var grids = document.querySelectorAll('.grid, .products-grid, .blog-grid, .stats-grid');
        var gridChildren = new Set();

        grids.forEach(function (grid) {
            var children = grid.querySelectorAll('.card, .product-card, .post-card, .stat-card, .feature-card, .dashboard-card');
            if (children.length) {
                children.forEach(function (child) { gridChildren.add(child); });
                gsap.from(children, {
                    opacity: 0,
                    y: 40,
                    filter: 'blur(6px)',
                    duration: 0.7,
                    stagger: 0.12,
                    ease: 'power2.out',
                    scrollTrigger: {
                        trigger: grid,
                        start: 'top 85%',
                        toggleActions: 'play none none none'
                    }
                });
            }
        });

        // Non-grid items
        targets.forEach(function (el) {
            if (gridChildren.has(el)) return;
            gsap.from(el, {
                opacity: 0,
                y: 40,
                filter: 'blur(6px)',
                duration: 0.7,
                ease: 'power2.out',
                scrollTrigger: {
                    trigger: el,
                    start: 'top 85%',
                    toggleActions: 'play none none none'
                }
            });
        });
    }

    // ────────────────────────────────────────────────────────────
    // 4. Parallax Scrolling (Enhanced)
    // ────────────────────────────────────────────────────────────
    function initParallax() {
        if (prefersReducedMotion) return;
        if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

        gsap.registerPlugin(ScrollTrigger);

        var mountainFar = document.querySelector('.xx-mountain-far');
        var mountainNear = document.querySelector('.xx-mountain-near');

        if (mountainFar) {
            gsap.to(mountainFar, {
                y: -80,
                scrollTrigger: {
                    trigger: document.body,
                    start: 'top top',
                    end: 'bottom bottom',
                    scrub: 1
                }
            });
        }

        if (mountainNear) {
            gsap.to(mountainNear, {
                y: -140,
                scrollTrigger: {
                    trigger: document.body,
                    start: 'top top',
                    end: 'bottom bottom',
                    scrub: 1
                }
            });
        }

        var heroContent = document.querySelector('.hero-content');
        if (heroContent) {
            gsap.to(heroContent, {
                y: 50,
                opacity: 0.7,
                scrollTrigger: {
                    trigger: heroContent,
                    start: 'top top',
                    end: 'bottom top',
                    scrub: 1
                }
            });
        }
    }

    // ────────────────────────────────────────────────────────────
    // 5. Spiritual Energy Vibration on Hover (Enhanced)
    // ────────────────────────────────────────────────────────────
    function initSpiritualVibration() {
        if (prefersReducedMotion) return;
        if (typeof gsap === 'undefined') return;

        var targets = document.querySelectorAll('.btn, .card, .product-card, .post-card');
        targets.forEach(function (el) {
            el.addEventListener('mouseenter', function () {
                // Subtle qi vibration
                gsap.to(el, {
                    x: '+=1.5', duration: 0.04, yoyo: true, repeat: 5,
                    ease: 'power2.inOut',
                    onComplete: function () { gsap.set(el, { x: 0 }); }
                });
                // Multi-layer spiritual glow
                gsap.to(el, {
                    boxShadow: '0 0 20px rgba(45, 212, 160, 0.4), 0 0 40px rgba(45, 212, 160, 0.15), 0 0 60px rgba(167, 139, 250, 0.08)',
                    duration: 0.3, ease: 'power2.out'
                });
            });
            el.addEventListener('mouseleave', function () {
                gsap.to(el, {
                    boxShadow: 'none', duration: 0.5, ease: 'power2.inOut'
                });
            });
        });
    }

    // ────────────────────────────────────────────────────────────
    // 6. Mist Dissolve Page Transition (Enhanced)
    // ────────────────────────────────────────────────────────────
    function initMistTransition() {
        if (prefersReducedMotion) return;
        if (typeof gsap === 'undefined') return;

        var overlay = document.getElementById('xx-mist-transition');
        if (!overlay) return;

        // On page load, dissolve the mist away with a qi glow
        overlay.style.opacity = '1';
        gsap.to(overlay, {
            opacity: 0,
            duration: 0.7,
            ease: 'power2.out',
            delay: 0.1
        });

        var activeTween = null;

        document.addEventListener('click', function (ev) {
            if (ev.button !== 0) return;
            var link = ev.target.closest('a');
            if (!link) return;
            if (link.hasAttribute('data-no-transition')) return;
            if (link.hasAttribute('download')) return;
            if (link.closest('form')) return;

            var href = link.getAttribute('href');
            if (!href) return;
            if (href.charAt(0) === '#') return;
            if (href.indexOf('javascript:') === 0) return;
            if (link.target === '_blank') return;

            try {
                var url = new URL(href, window.location.origin);
                if (url.origin !== window.location.origin) return;
            } catch (e) {
                return;
            }

            ev.preventDefault();

            if (activeTween) {
                activeTween.kill();
            }

            activeTween = gsap.to(overlay, {
                opacity: 1,
                duration: 0.35,
                ease: 'power2.in',
                onComplete: function () {
                    activeTween = null;
                    window.location = href;
                }
            });
        });
    }

    // ────────────────────────────────────────────────────────────
    // 7. Bloom Effect on GodCoin button and active icons
    // ────────────────────────────────────────────────────────────
    function initBloomEffect() {
        if (prefersReducedMotion) return;
        if (typeof gsap === 'undefined') return;

        var bloomElements = document.querySelectorAll('.xx-bloom');
        bloomElements.forEach(function (el) {
            gsap.to(el, {
                boxShadow: '0 0 20px rgba(45, 212, 160, 0.5), 0 0 40px rgba(251, 191, 36, 0.25), 0 0 60px rgba(167, 139, 250, 0.1)',
                duration: 1.5,
                repeat: -1,
                yoyo: true,
                ease: 'sine.inOut'
            });
        });
    }

    // ────────────────────────────────────────────────────────────
    // Boot
    // ────────────────────────────────────────────────────────────
    function boot() {
        if (prefersReducedMotion) return;

        try { initCherryBlossoms(); }       catch (e) { /* non-fatal */ }
        try { initFloatingElements(); }     catch (e) { /* non-fatal */ }
        try { initScrollAnimations(); }     catch (e) { /* non-fatal */ }
        try { initParallax(); }             catch (e) { /* non-fatal */ }
        try { initSpiritualVibration(); }   catch (e) { /* non-fatal */ }
        try { initMistTransition(); }       catch (e) { /* non-fatal */ }
        try { initBloomEffect(); }          catch (e) { /* non-fatal */ }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
