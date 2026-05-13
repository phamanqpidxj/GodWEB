// GodWeb - Main JavaScript

function initializeScrollReveal() {
    const revealTargets = document.querySelectorAll('.section, .page-header, .card, .blog-content, .comments-section, .stat-card, .search-bar, .pagination, .footer-section');

    revealTargets.forEach((el, index) => {
        el.classList.add('reveal');
        const tier = index % 4;
        if (tier > 0) {
            el.classList.add(`reveal-delay-${tier}`);
        }
    });

    if (!('IntersectionObserver' in window)) {
        revealTargets.forEach(el => el.classList.add('revealed'));
        return;
    }

    // Anything already in (or near) the viewport at load time is
    // revealed immediately. This is critical for elements that are
    // taller than the viewport (e.g. long blog post content):
    // a percentage-based intersection threshold could never fire
    // because their visible slice is always smaller than the
    // threshold ratio, leaving them stuck at opacity: 0.
    const viewportH = window.innerHeight || document.documentElement.clientHeight;
    const isInOrNearViewport = el => {
        const rect = el.getBoundingClientRect();
        return rect.top < viewportH + 200 && rect.bottom > -200;
    };
    const isTallerThanViewport = el => el.getBoundingClientRect().height >= viewportH * 0.9;

    const toObserve = [];
    revealTargets.forEach(el => {
        if (isInOrNearViewport(el) || isTallerThanViewport(el)) {
            el.classList.add('revealed');
        } else {
            toObserve.push(el);
        }
    });

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, {
        // Use threshold 0 so any pixel of the element entering the
        // viewport reveals it. The previous 14% threshold could
        // never be reached on tall elements (max intersection ratio
        // = viewportHeight / elementHeight) which is exactly why
        // long blog posts disappeared on narrow displays.
        threshold: 0,
        rootMargin: '0px 0px -5% 0px'
    });

    toObserve.forEach(el => observer.observe(el));

    // Final safety net: if anything remains hidden 1.5s after load
    // (e.g. observer never fired), force-reveal it so users always
    // see the content.
    setTimeout(() => {
        revealTargets.forEach(el => {
            if (!el.classList.contains('revealed')) {
                el.classList.add('revealed');
            }
        });
    }, 1500);
}

function initializeParallaxHero() {
    const hero = document.querySelector('.hero');
    if (!hero) {
        return;
    }

    window.addEventListener('scroll', () => {
        const offset = Math.min(window.scrollY * 0.18, 42);
        hero.style.transform = `translateY(${offset}px)`;
    }, { passive: true });
}

function initializeCardTilt() {
    const cards = document.querySelectorAll('.card');

    cards.forEach(card => {
        card.addEventListener('mousemove', event => {
            if (window.innerWidth < 992) {
                return;
            }

            const bounds = card.getBoundingClientRect();
            const x = event.clientX - bounds.left;
            const y = event.clientY - bounds.top;
            const centerX = bounds.width / 2;
            const centerY = bounds.height / 2;
            const rotateX = ((y - centerY) / centerY) * -4;
            const rotateY = ((x - centerX) / centerX) * 4;

            card.style.transform = `translateY(-6px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });
}

function initializeButtonRipple() {
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(button => {
        button.addEventListener('click', event => {
            const circle = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);

            circle.classList.add('btn-ripple');
            circle.style.width = `${size}px`;
            circle.style.height = `${size}px`;
            circle.style.left = `${event.clientX - rect.left - size / 2}px`;
            circle.style.top = `${event.clientY - rect.top - size / 2}px`;

            const existingRipple = button.querySelector('.btn-ripple');
            if (existingRipple) {
                existingRipple.remove();
            }

            button.appendChild(circle);
            circle.addEventListener('animationend', () => circle.remove(), { once: true });
        });
    });
}

function updateNotificationBadge(newCount) {
    const desktopBadge = document.getElementById('notificationBadge');
    const mobileBadge = document.getElementById('mobileNotificationCount');

    if (desktopBadge) {
        desktopBadge.textContent = String(newCount);
        desktopBadge.classList.toggle('hidden', newCount <= 0);
    }

    if (mobileBadge) {
        mobileBadge.textContent = String(newCount);
        mobileBadge.setAttribute('data-count', String(newCount));
        if (newCount <= 0) {
            mobileBadge.textContent = '';
        }
    }
}

function initializeNotificationActions() {
    const notificationItems = document.querySelectorAll('.notification-item[data-notification-id]');
    notificationItems.forEach(item => {
        item.addEventListener('click', async function() {
            const notificationId = this.dataset.notificationId;
            if (!notificationId) {
                return;
            }

            try {
                const response = await fetch(`/notifications/${notificationId}/read`, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!response.ok) {
                    return;
                }

                const result = await response.json();
                if (result.success) {
                    this.classList.remove('unread');
                    updateNotificationBadge(result.unread_count || 0);
                }
            } catch (error) {
                console.error('Notification read error:', error);
            }
        });
    });
}

function toggleNotificationFromMobile() {
    const notificationDropdown = document.getElementById('notificationDropdown');
    if (notificationDropdown) {
        notificationDropdown.classList.toggle('active');
    }
}

// Mobile Menu Toggle Function
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileOverlay = document.getElementById('mobileMenuOverlay');

    if (mobileMenu && mobileOverlay) {
        mobileMenu.classList.toggle('active');
        mobileOverlay.classList.toggle('active');

        // Prevent body scroll when menu is open
        if (mobileMenu.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
}

// Close mobile menu when clicking on a link
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuLinks = document.querySelectorAll('.mobile-menu-links a');
    mobileMenuLinks.forEach(link => {
        link.addEventListener('click', function() {
            toggleMobileMenu();
        });
    });

    // Dropdown menu click toggle
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const btn = dropdown.querySelector('.btn, .notification-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');

        if (btn) {
            // Click to toggle
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                // Close all other dropdowns
                dropdowns.forEach(d => {
                    if (d !== dropdown) d.classList.remove('active');
                });
                // Toggle current dropdown
                dropdown.classList.toggle('active');
            });
        }

        // Mouse enter - show dropdown
        dropdown.addEventListener('mouseenter', function() {
            dropdown.classList.add('active');
        });

        // Mouse leave - hide dropdown after delay
        dropdown.addEventListener('mouseleave', function() {
            setTimeout(() => {
                if (!dropdown.matches(':hover')) {
                    dropdown.classList.remove('active');
                }
            }, 100);
        });

        // Keep dropdown open when hovering over menu
        if (menu) {
            menu.addEventListener('mouseenter', function() {
                dropdown.classList.add('active');
            });

            menu.addEventListener('mouseleave', function() {
                dropdown.classList.remove('active');
            });
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            dropdowns.forEach(d => d.classList.remove('active'));
        }
    });

    // Auto hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm || 'Bạn có chắc chắn muốn thực hiện hành động này?')) {
                e.preventDefault();
            }
        });
    });

    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.navbar-menu');
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetSelector = this.getAttribute('href');
            if (!targetSelector || targetSelector === '#') {
                return;
            }

            e.preventDefault();
            const target = document.querySelector(targetSelector);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (form.dataset.submitting === 'true') {
                e.preventDefault();
                return;
            }

            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = 'var(--danger-color)';
                } else {
                    field.style.borderColor = '';
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Vui lòng điền đầy đủ các trường bắt buộc!');
                return;
            }

            if ((form.method || 'GET').toUpperCase() === 'GET') {
                return;
            }

            form.dataset.submitting = 'true';
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!submitButton) {
                return;
            }

            submitButton.disabled = true;
            submitButton.classList.add('is-loading');

            if (submitButton.tagName === 'BUTTON') {
                if (!submitButton.dataset.originalText) {
                    submitButton.dataset.originalText = submitButton.innerHTML;
                }
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
            } else {
                if (!submitButton.dataset.originalText) {
                    submitButton.dataset.originalText = submitButton.value;
                }
                submitButton.value = 'Đang xử lý...';
            }
        });
    });

    // Copy to clipboard functionality
    document.querySelectorAll('[data-copy]').forEach(elem => {
        elem.addEventListener('click', function() {
            const text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Đã copy!';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    });

    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        initializeScrollReveal();
        initializeParallaxHero();
        initializeCardTilt();
        initializeButtonRipple();
    }

    initializeNotificationActions();
});

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Calculate GodCoin from VND
function calculateGodCoin(vnd) {
    return Math.floor(vnd / 1000);
}

// ========================================
// DARK MODE / LIGHT MODE TOGGLE
// Default state = DARK. localStorage key: "siteTheme" with values "light"|"dark".
// <html> carries theme-light / theme-dark (modern selectors). The legacy
// "light-mode" class is kept on <body> only (that is where every existing
// body.light-mode CSS rule matches). Icon visibility is CSS-driven - both
// SVGs are always in the DOM.
// ========================================

function _syncThemeA11yLabels(isLight) {
    // User-facing label describes the ACTION the click will take.
    var btn = document.getElementById('toggleSiteTheme');
    var mBtn = document.getElementById('mobileThemeToggle');
    var nextLabel = isLight ? 'Chuy\u1ec3n sang ch\u1ebf \u0111\u1ed9 t\u1ed1i'
                            : 'Chuy\u1ec3n sang ch\u1ebf \u0111\u1ed9 s\u00e1ng';
    if (btn) {
        btn.setAttribute('aria-label', nextLabel);
        btn.setAttribute('title', nextLabel);
    }
    if (mBtn) {
        mBtn.setAttribute('aria-label', nextLabel);
    }
}

// "World Shift" transition: pulse the existing #xx-mist-transition
// overlay so flipping between the Heavenly Court and the Blood Mist
// Underworld feels like an ink-wash dissolving the realm. The CSS
// hook (`html.xx-world-shifting`) lives in xianxia-celestial-path.css
// §15. Self-clears via animationend so re-toggles always re-trigger.
function _triggerWorldShift() {
    var root = document.documentElement;
    if (!root) return;
    var reduceMotion = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) return;

    if (root.classList.contains('xx-world-shifting')) {
        root.classList.remove('xx-world-shifting');
        /* force a reflow so the animation re-runs */
        // eslint-disable-next-line no-unused-expressions
        void root.offsetWidth;
    }
    root.classList.add('xx-world-shifting');
    var overlay = document.getElementById('xx-mist-transition');
    if (!overlay) {
        window.setTimeout(function () {
            root.classList.remove('xx-world-shifting');
        }, 950);
        return;
    }
    var clear = function () {
        root.classList.remove('xx-world-shifting');
        overlay.removeEventListener('animationend', clear);
    };
    overlay.addEventListener('animationend', clear, { once: true });
    /* Safety net in case animationend never fires (e.g. display:none
     * overlay in a partial template) — clears the hook after the
     * keyframe's nominal duration. */
    window.setTimeout(clear, 1100);
}

function toggleSiteTheme() {
    var root = document.documentElement;
    var body = document.body;
    var wasLight = root.classList.contains('theme-light');
    var isLight = !wasLight;

    _triggerWorldShift();

    root.classList.toggle('theme-light', isLight);
    root.classList.toggle('theme-dark', !isLight);
    if (body) {
        body.classList.toggle('light-mode', isLight);
    }

    try {
        localStorage.setItem('siteTheme', isLight ? 'light' : 'dark');
    } catch (e) {
        /* private mode / storage disabled - swallow */
    }

    _syncThemeA11yLabels(isLight);
}

function toggleSiteThemeFromMobile() {
    toggleSiteTheme();
}

document.addEventListener('DOMContentLoaded', function() {
    var themeBtn = document.getElementById('toggleSiteTheme');
    var isLight = document.documentElement.classList.contains('theme-light');
    _syncThemeA11yLabels(isLight);
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleSiteTheme);
    }
});

// ────────────────────────────────────────────────────────────
// Pause Immortal-card auras while they're scrolled off-screen.
// Each `.xx-immortal-card::before` runs a conic-gradient rotation
// AND a drop-shadow filter pulse. With a dozen VIP posts on a
// listing page, that's a measurable paint cost every frame even
// when the user is looking at the footer. IntersectionObserver
// flips a class that pins `animation-play-state: paused` so the
// browser can skip the work.
// ────────────────────────────────────────────────────────────
function initializeImmortalAuraVisibility() {
    if (!('IntersectionObserver' in window)) return;

    var cards = document.querySelectorAll('.xx-immortal-card');
    if (!cards.length) return;

    // Start paused; observer will un-pause anything actually visible.
    cards.forEach(function (card) { card.classList.add('xx-aura-paused'); });

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            entry.target.classList.toggle('xx-aura-paused', !entry.isIntersecting);
        });
    }, { rootMargin: '120px 0px' });

    cards.forEach(function (card) { observer.observe(card); });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeImmortalAuraVisibility);
} else {
    initializeImmortalAuraVisibility();
}

