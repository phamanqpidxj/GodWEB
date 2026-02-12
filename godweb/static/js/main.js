// GodWeb - Main JavaScript

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
        const btn = dropdown.querySelector('.btn');
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
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
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

