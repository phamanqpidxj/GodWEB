"""Regression tests for the Celestial Path UI/UX overhaul (FEAT-002).

The overhaul layers three things on top of the existing Xianxia theme:

1.  A rotating Yin-Yang (Taiji) ring wraps the existing moon/sun SVGs in
    both ``#toggleSiteTheme`` and ``#mobileThemeToggle``.  The pre-existing
    icon contract (no Font Awesome gear, both SVGs always in the DOM)
    from ``tests/test_theme_toggle.py`` must continue to hold.

2.  Blog post cards on the index/home pages render with either
    ``xx-immortal-card`` (premium) or ``xx-mortal-card`` (free) so the
    Mortal/Immortal visual fork the brief asks for is data-driven.

3.  ``xianxia-celestial-path.css`` ships globally — that's where the
    dark-mode "no black text" safety net and the Yin-Yang rotation live.
"""
from __future__ import annotations

import re
from pathlib import Path

from tests.conftest import extract_csrf_token


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = REPO_ROOT / 'godweb' / 'static' / 'css' / 'xianxia-celestial-path.css'


def _login_html(client) -> str:
    response = client.get('/auth/login')
    assert response.status_code == 200
    return response.data.decode('utf-8')


def _toggle_inner_html(html: str, element_id: str, tag: str) -> str:
    pattern = rf'<{tag}[^>]*id="{element_id}"[^>]*>(.*?)</{tag}>'
    match = re.search(pattern, html, re.DOTALL)
    assert match, f'#{element_id} not rendered as <{tag}>'
    return match.group(1)


# ────────────────────────────────────────────────────────────────────
# 1. Yin-Yang ring wraps the moon/sun icons in both toggles
# ────────────────────────────────────────────────────────────────────
def test_desktop_toggle_renders_yinyang_ring(client):
    inner = _toggle_inner_html(_login_html(client), 'toggleSiteTheme', 'button')
    assert 'class="theme-yinyang-ring"' in inner, (
        'desktop theme toggle must render a Yin-Yang ring wrapper'
    )
    # The ring is an SVG, not a Font Awesome glyph.
    assert '<svg' in inner.split('theme-yinyang-ring')[1].split('</span>')[0]
    # The pre-existing icon contract still holds — both moon and sun
    # SVG wrappers must remain in the DOM alongside the ring.
    assert 'class="theme-icon-moon"' in inner
    assert 'class="theme-icon-sun"' in inner


def test_mobile_toggle_renders_yinyang_ring(client):
    inner = _toggle_inner_html(_login_html(client), 'mobileThemeToggle', 'a')
    assert 'class="theme-yinyang-ring"' in inner, (
        'mobile theme toggle must render a Yin-Yang ring wrapper'
    )
    assert 'class="theme-icon-moon"' in inner
    assert 'class="theme-icon-sun"' in inner


def test_yinyang_ring_never_renders_a_gear(client):
    """The whole point of the ring is to replace the historical gear
    fallback. ``fa-cog`` / ``fa-gear`` must not appear anywhere inside
    either toggle, including inside the new ring markup.
    """
    html = _login_html(client)
    for element_id, tag in (('toggleSiteTheme', 'button'),
                             ('mobileThemeToggle', 'a')):
        inner = _toggle_inner_html(html, element_id, tag)
        assert 'fa-cog' not in inner
        assert 'fa-gear' not in inner


# ────────────────────────────────────────────────────────────────────
# 2. Celestial Path stylesheet is wired into base.html
# ────────────────────────────────────────────────────────────────────
def test_celestial_path_stylesheet_is_linked(client):
    html = _login_html(client)
    assert 'css/xianxia-celestial-path.css' in html, (
        'base.html must link xianxia-celestial-path.css so the Yin-Yang '
        'rotation, dark-text safety net and immortal-card aura ship to '
        'every page'
    )


def test_celestial_path_stylesheet_loads_after_card_contrast_fix(client):
    """The new stylesheet has to override `card-contrast-fix.css` (which
    sets text colors first) so it must be linked *after* it. If the order
    flips, the dark-mode safety net would lose to card-contrast-fix.
    """
    html = _login_html(client)
    fix_idx = html.find('card-contrast-fix.css')
    cp_idx = html.find('xianxia-celestial-path.css')
    assert fix_idx != -1 and cp_idx != -1
    assert cp_idx > fix_idx, (
        'xianxia-celestial-path.css must be linked after card-contrast-fix.css'
    )


# ────────────────────────────────────────────────────────────────────
# 3. Dark-mode "no black text" rules exist in the stylesheet
# ────────────────────────────────────────────────────────────────────
def test_dark_mode_text_safety_net_in_stylesheet():
    source = CSS_PATH.read_text(encoding='utf-8')
    # The safety-net rule must target every heading level + p inside
    # the html.theme-dark scope. Reading the source text is the cheapest
    # cross-browser regression guard we can write without a real browser.
    assert 'html.theme-dark' in source, (
        'xianxia-celestial-path.css must scope its dark-mode text rules '
        'under html.theme-dark so they only apply in the Demonic Realm'
    )
    for selector in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'):
        assert f'html.theme-dark {selector}' in source, (
            f'html.theme-dark {selector} rule missing — dark-mode text '
            f'must be promoted to the silver-white default'
        )


def test_yinyang_rotation_rule_exists():
    source = CSS_PATH.read_text(encoding='utf-8')
    # In dark mode the ring is at 0deg, in light mode 180deg — the
    # design brief says it must "rotate 180 degrees" on toggle.
    assert 'html.theme-light .theme-yinyang-ring' in source
    assert 'rotate(180deg)' in source, (
        'Yin-Yang ring must rotate 180deg between realms'
    )


def test_immortal_aura_overrides_legacy_premium_pulse():
    """The legacy ``.card:has(.premium-badge)::before`` rule in
    ``xianxia-theme.css`` has specificity (0,2,0). Our Celestial Path
    aura must match that with the compound ``.card.xx-immortal-card``
    selector so the new conic ``xxImmortalAura`` actually wins —
    otherwise the rotating Linh-Khí ring silently degrades to the old
    static opacity pulse.
    """
    source = CSS_PATH.read_text(encoding='utf-8')
    assert '.card.xx-immortal-card::before' in source, (
        'aura ::before rule must use .card.xx-immortal-card to match '
        'the legacy :has(.premium-badge) selector specificity'
    )
    assert '.card.xx-immortal-card::after' in source, (
        'aura ::after halo must match the legacy specificity too'
    )
    assert 'animation: xxImmortalAura' in source, (
        'the conic-gradient aura must be driven by xxImmortalAura, '
        'not the legacy xxVipAuraPulse'
    )

    # In light mode (``body.light-mode``), ``xianxia-theme-light.css``
    # re-pins ``animation: xxVipAuraPulseLight`` on the same
    # ``::before`` pseudo-element. Our light-mode override must
    # explicitly re-pin the rotation animation, otherwise the aura
    # silently degrades to an opacity pulse only in the Heavenly Realm.
    light_block_idx = source.find('body.light-mode .card.xx-immortal-card::before')
    assert light_block_idx != -1, (
        'light-mode aura override must use the .card.xx-immortal-card '
        'compound selector to match legacy specificity'
    )
    light_block = source[light_block_idx:light_block_idx + 800]
    assert 'xxImmortalAura' in light_block, (
        'light-mode aura ::before block must re-declare animation: '
        'xxImmortalAura so it does not fall back to xxVipAuraPulseLight'
    )

    # In dark mode the legacy ``.card:has(.premium-badge):hover::before``
    # rule in ``xianxia-theme.css`` sets ``animation: none``. Our hover
    # override must use the shorthand ``animation:`` (not the
    # ``animation-duration`` longhand) so the rotating aura keeps spinning
    # and just speeds up on hover.
    hover_idx = source.find('.card.xx-immortal-card:hover::before')
    assert hover_idx != -1, (
        'dark-mode hover speed-up must use .card.xx-immortal-card to '
        'match legacy :hover specificity'
    )
    hover_block = source[hover_idx:hover_idx + 400]
    assert 'animation: xxImmortalAura' in hover_block, (
        'hover ::before block must use the `animation:` shorthand to '
        'override the legacy `animation: none` rule; otherwise the aura '
        'silently stops rotating on hover'
    )


# ────────────────────────────────────────────────────────────────────
# 4. Mortal / Immortal post cards on the blog index
# ────────────────────────────────────────────────────────────────────
def _login(client, email: str, password: str):
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    return client.post(
        '/auth/login',
        data={'email': email, 'password': password, 'csrf_token': token},
        follow_redirects=False,
    )


def _seed_user(app, email='ctest_user@example.com', password='Password1!'):
    from godweb.extensions import db
    from godweb.models import User

    with app.app_context():
        user = User(
            username='ctest_user',
            email=email,
            recovery_number='1234',
            godcoin_balance=0,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    return email, password


def _seed_posts(app):
    """Insert one premium and one free post so the blog index has
    enough data to render both variants."""
    from godweb.extensions import db
    from godweb.models import Category, Post, User

    with app.app_context():
        admin = User(
            username='ctest_admin',
            email='ctest_admin@example.com',
            role='admin',
        )
        admin.set_password('Password1!')
        db.session.add(admin)
        db.session.flush()

        category = Category(name='Tin tức Tu Tiên')
        db.session.add(category)
        db.session.flush()

        mortal = Post(
            title='Bài viết phàm nhân',
            content='Nội dung phàm nhân.',
            author_id=admin.id,
            category_id=category.id,
            is_premium=False,
            premium_price=0,
        )
        immortal = Post(
            title='Bí kíp Tiên Nhân',
            content='Nội dung Tiên Nhân.',
            author_id=admin.id,
            category_id=category.id,
            is_premium=True,
            premium_price=99,
        )
        db.session.add_all([mortal, immortal])
        db.session.commit()


def test_blog_index_marks_mortal_and_immortal_cards(app, client):
    """The blog index filters by `type` (`free` vs `premium`). Each
    filtered view must render its cards with the corresponding variant
    so the Mortal/Immortal fork holds on both tabs.
    """
    email, password = _seed_user(app)
    _seed_posts(app)
    _login(client, email, password)

    free_resp = client.get('/blog/?type=free')
    assert free_resp.status_code == 200
    free_html = free_resp.data.decode('utf-8')
    assert 'xx-mortal-card' in free_html, (
        'free blog posts must render with the Mortal (bamboo scroll) '
        'card variant'
    )
    assert 'xx-immortal-card' not in free_html, (
        'the Mortal tab must not render Immortal-styled cards'
    )

    premium_resp = client.get('/blog/?type=premium')
    assert premium_resp.status_code == 200
    premium_html = premium_resp.data.decode('utf-8')
    assert 'xx-immortal-card' in premium_html, (
        'premium blog posts must render with the Immortal (linh-khi '
        'aura) card variant'
    )
    # The mist drift overlay is only emitted inside Immortal cards.
    assert 'xx-immortal-mist' in premium_html


def test_store_cards_use_mortal_variant(app, client):
    """All store products fall back to the Mortal variant — the codebase
    has no `is_premium` flag on Product, but the bamboo-scroll look is
    still the right baseline so cards don't look flat next to blog ones.
    """
    from godweb.extensions import db
    from godweb.models import Product

    email, password = _seed_user(app)
    _login(client, email, password)

    with app.app_context():
        product = Product(
            name='Linh Thạch',
            description='Đá nguyên liệu tu luyện.',
            price=10,
            stock=5,
        )
        db.session.add(product)
        db.session.commit()

    response = client.get('/store/')
    assert response.status_code == 200
    assert b'xx-mortal-card' in response.data
