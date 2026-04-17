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

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.14,
        rootMargin: '0px 0px -8% 0px'
    });

    revealTargets.forEach(el => observer.observe(el));
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
// DARK MODE TOGGLE
// ========================================
function toggleSiteTheme() {
    const body = document.body;
    const themeBtn = document.getElementById('toggleSiteTheme');
    const mobileThemeBtn = document.getElementById('mobileThemeToggle');

    body.classList.toggle('dark-mode');

    if (body.classList.contains('dark-mode')) {
        localStorage.setItem('siteTheme', 'dark');
        if (themeBtn) themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
        if (mobileThemeBtn) mobileThemeBtn.innerHTML = '<i class="fas fa-sun"></i> Chế độ sáng';
    } else {
        localStorage.setItem('siteTheme', 'light');
        if (themeBtn) themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
        if (mobileThemeBtn) mobileThemeBtn.innerHTML = '<i class="fas fa-moon"></i> Chế độ tối';
    }
}

// Function for mobile menu theme toggle
function toggleSiteThemeFromMobile() {
    toggleSiteTheme();
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('siteTheme');
    const themeBtn = document.getElementById('toggleSiteTheme');
    const mobileThemeBtn = document.getElementById('mobileThemeToggle');

    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (themeBtn) themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
        if (mobileThemeBtn) mobileThemeBtn.innerHTML = '<i class="fas fa-sun"></i> Chế độ sáng';
    }

    // Add click event to desktop theme toggle button
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleSiteTheme);
    }
});

