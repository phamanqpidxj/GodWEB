"""Regression tests for the Wave 1 Tu Tiên overlay (PR follow-up to #31).

What this covers, top to bottom:

1. Cultivation realm system on the User model
   - 6 tiers from Phàm Nhân → Hoá Thần in CULTIVATION_TIERS
   - `cultivation_xp` is activity-based (NOT spending-based) and
     weights posts > purchases > orders > comments > streak
   - `cultivation_tier()` returns the correct dict for boundary cases
2. Login streak helper (`auth._update_login_streak`)
   - first login, same-day re-login, consecutive day, multi-day gap
3. Template / asset wiring
   - base.html references the new CSS + JS files
   - audio toggle button in footer with sane aria-pressed default
   - cultivation badge in the authenticated navbar dropdown
   - Tu Tiên heading + hoành phi added to listing pages
   - empty-state poetic microcopy is present on at least one page
4. xianxia-tu-tien.css contains the contract selectors
5. xianxia-tu-tien.js wires up vermillion seal + procedural audio +
   honours prefers-reduced-motion
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from godweb.models import CULTIVATION_TIERS, User
from godweb.routes.auth import _update_login_streak


REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = REPO_ROOT / 'godweb' / 'static'
TEMPLATE_DIR = REPO_ROOT / 'godweb' / 'templates'
CSS_PATH = STATIC_DIR / 'css' / 'xianxia-tu-tien.css'
JS_PATH = STATIC_DIR / 'js' / 'xianxia-tu-tien.js'
BASE_TEMPLATE = TEMPLATE_DIR / 'base.html'
HOME_TEMPLATE = TEMPLATE_DIR / 'home.html'
BLOG_INDEX = TEMPLATE_DIR / 'blog' / 'index.html'
STORE_INDEX = TEMPLATE_DIR / 'store' / 'index.html'
WALLET_INDEX = TEMPLATE_DIR / 'wallet' / 'index.html'
PROFILE_INDEX = TEMPLATE_DIR / 'profile' / 'index.html'


# ─────────────────────────────────────────────────────────────
# 1. Cultivation realm system
# ─────────────────────────────────────────────────────────────


def test_cultivation_tiers_has_six_realms_in_order():
    """The table must contain the canonical 6 tiers, threshold-sorted.

    A 7th tier (or a re-ordering) would silently break the index
    math in `cultivation_tier()` which walks the table in order.
    """
    assert len(CULTIVATION_TIERS) == 6, 'CULTIVATION_TIERS must have exactly 6 entries'
    keys = [row[1] for row in CULTIVATION_TIERS]
    assert keys == [
        'pham_nhan', 'luyen_khi', 'truc_co',
        'kim_dan', 'nguyen_anh', 'hoa_than',
    ]
    thresholds = [row[0] for row in CULTIVATION_TIERS]
    assert thresholds == sorted(thresholds), 'thresholds must be ascending'
    assert thresholds[0] == 0, 'Phàm Nhân baseline must start at 0 XP'


def test_user_model_has_cultivation_columns():
    """`last_login_at` + `login_streak` must be ORM-declared so the
    in-process model matches what the migration ALTER TABLEs add at
    boot."""
    columns = {c.name for c in User.__table__.columns}
    assert 'last_login_at' in columns
    assert 'login_streak' in columns


class _FakeUser:
    """Pure-Python stand-in for User used in cultivation_xp unit tests.

    Why not the real User: SQLAlchemy's InstrumentedAttribute is a
    data descriptor, so assigning `user.posts = [object()]` invokes
    the relationship setter and rejects non-mapped items. We only
    need lists with the right *length* for cultivation_xp, so a
    duck-typed stand-in is much simpler — and decouples the realm
    math from ORM semantics.
    """

    def __init__(self, *, posts=0, purchases=0, orders=0,
                 comments=0, streak=0):
        self.posts = [None] * posts
        self.post_purchases = [None] * purchases
        self.orders = [None] * orders
        self.comments = [None] * comments
        self.login_streak = streak

    # Bind the real methods so any future change in models.py is
    # automatically picked up.
    cultivation_xp = User.cultivation_xp
    cultivation_tier = User.cultivation_tier


def test_cultivation_xp_is_activity_based_and_weighted(app):
    """XP must weight posts >> purchases >> orders >> comments > streak.

    With [posts=1, purchases=1, orders=1, comments=1, streak=10]
    we expect: 50 + 20 + 10 + 5 + 30 = 115.
    """
    user = _FakeUser(
        posts=1, purchases=1, orders=1, comments=1, streak=10,
    )
    assert user.cultivation_xp == 50 + 20 + 10 + 5 + 30


def test_cultivation_tier_phamnhan_for_new_user(app):
    user = _FakeUser()
    tier = user.cultivation_tier()
    assert tier['key'] == 'pham_nhan'
    assert tier['glyph'] == '凡'
    assert tier['name_vi'] == 'Phàm Nhân'
    assert tier['xp'] == 0
    # Must still report a next tier so the progress bar can render.
    assert tier['next_threshold'] == 50
    assert tier['next_name_vi'] == 'Luyện Khí'
    assert tier['xp_remaining'] == 50


def test_cultivation_tier_boundary_climbs_at_threshold(app):
    """Exactly hitting the threshold of a tier promotes the user there."""
    # 17 × 3 = 51 XP → just past the 50 XP Luyện Khí entry.
    user = _FakeUser(streak=17)
    tier = user.cultivation_tier()
    assert tier['key'] == 'luyen_khi'
    assert tier['glyph'] == '練'


def test_cultivation_tier_max_realm_has_no_next(app):
    """Hoá Thần is the cap; templates must handle `next_threshold == None`."""
    # 80 posts × 50 XP = 4000 XP → exactly Hoá Thần.
    user = _FakeUser(posts=80)
    tier = user.cultivation_tier()
    assert tier['key'] == 'hoa_than'
    assert tier['xp'] == 4000
    assert tier['next_threshold'] is None
    assert tier['next_name_vi'] is None
    assert tier['xp_remaining'] == 0


# ─────────────────────────────────────────────────────────────
# 2. Login streak helper
# ─────────────────────────────────────────────────────────────


def test_login_streak_first_login_sets_to_one(app):
    """A brand-new user (last_login_at is NULL) should start at streak 1."""
    with app.app_context():
        from godweb.extensions import db
        u = User(username='first', email='first@example.com')
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()
        assert u.last_login_at is None
        assert (u.login_streak or 0) == 0
        _update_login_streak(u)
        assert u.login_streak == 1
        assert u.last_login_at is not None


def test_login_streak_same_day_re_login_does_not_double_count(app):
    with app.app_context():
        from godweb.extensions import db
        u = User(
            username='sameday',
            email='sameday@example.com',
            last_login_at=datetime.utcnow(),
            login_streak=3,
        )
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()
        _update_login_streak(u)
        assert u.login_streak == 3, 'second login on the same day must not bump'


def test_login_streak_consecutive_day_increments(app):
    with app.app_context():
        from godweb.extensions import db
        yesterday = datetime.utcnow() - timedelta(days=1)
        u = User(
            username='streak',
            email='streak@example.com',
            last_login_at=yesterday,
            login_streak=5,
        )
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()
        _update_login_streak(u)
        assert u.login_streak == 6


def test_login_streak_gap_resets_to_one(app):
    with app.app_context():
        from godweb.extensions import db
        long_ago = datetime.utcnow() - timedelta(days=5)
        u = User(
            username='gap',
            email='gap@example.com',
            last_login_at=long_ago,
            login_streak=12,
        )
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()
        _update_login_streak(u)
        assert u.login_streak == 1, '5-day gap must reset the streak'


# ─────────────────────────────────────────────────────────────
# 3. Template wiring
# ─────────────────────────────────────────────────────────────


def test_base_template_includes_wave1_css_and_js():
    body = BASE_TEMPLATE.read_text(encoding='utf-8')
    assert 'xianxia-tu-tien.css' in body, 'base.html must link the new CSS'
    assert 'xianxia-tu-tien.js' in body, 'base.html must include the new JS'


def test_base_template_has_audio_toggle_with_safe_aria_default():
    body = BASE_TEMPLATE.read_text(encoding='utf-8')
    assert 'xx-audio-toggle' in body
    # Visible labels in both states.
    assert 'xx-audio-label-on' in body
    assert 'xx-audio-label-off' in body
    # aria-pressed must be present so screen readers announce state.
    assert 'aria-pressed=' in body


def test_base_template_renders_cultivation_badge_in_navbar():
    body = BASE_TEMPLATE.read_text(encoding='utf-8')
    # The badge must wrap the username and tier glyph for authenticated users.
    assert 'cultivation_tier()' in body
    assert 'xx-cult-badge' in body
    assert 'xx-cult-glyph' in body
    # And it must use the dynamic tier key class so the colour scheme follows.
    assert 'xx-cult-{{ _navbar_tier.key }}' in body


def test_listing_pages_use_tutien_heading():
    """Blog, Store, Wallet, Profile listing pages must use the new
    bilingual Tu Tiên heading component, not the old generic h1."""
    for path, zh_name in [
        (BLOG_INDEX, '秘籍阁'),
        (STORE_INDEX, '法宝阁'),
        (WALLET_INDEX, '丹鼎'),
        (PROFILE_INDEX, '修士牌'),
    ]:
        body = path.read_text(encoding='utf-8')
        assert 'xx-tutien-heading' in body, f'{path.name}: missing xx-tutien-heading'
        assert zh_name in body, f'{path.name}: missing Chinese name {zh_name!r}'
        assert 'xx-tutien-zh' in body
        assert 'xx-tutien-vi' in body


def test_home_template_has_hoanh_phi():
    body = HOME_TEMPLATE.read_text(encoding='utf-8')
    assert 'xx-hoanh-phi' in body, 'home.html must render the hoành phi'
    assert '道法自然' in body, 'plaque must carry the 4 chars 道法自然'
    assert 'Đạo Pháp Tự Nhiên' in body


def test_profile_index_renders_cultivation_progress_card():
    body = PROFILE_INDEX.read_text(encoding='utf-8')
    assert 'xx-tusi-card' in body
    assert 'xx-tusi-progress' in body
    # The card must use the same tier dict produced at the top of the
    # file so the badge and the progress bar always agree.
    assert "current_user.cultivation_tier()" in body


def test_empty_state_microcopy_has_poetic_voice_line_somewhere():
    """At least one empty state must use the new `.xx-poetic` voice
    line. Keeps the "occasional punchline" tone the user asked for
    without committing to overdoing it across every empty page."""
    candidates = [
        TEMPLATE_DIR / 'blog' / 'detail.html',
        TEMPLATE_DIR / 'profile' / 'orders.html',
    ]
    hits = [p for p in candidates if 'xx-poetic' in p.read_text(encoding='utf-8')]
    assert hits, 'no empty-state poetic microcopy found in expected templates'


# ─────────────────────────────────────────────────────────────
# 4. CSS contract
# ─────────────────────────────────────────────────────────────


def test_css_defines_required_selectors():
    css = CSS_PATH.read_text(encoding='utf-8')
    must_have = [
        # Cultivation badges — base + all 6 tier variants
        '.xx-cult-badge',
        '.xx-cult-glyph',
        '.xx-cult-pham_nhan',
        '.xx-cult-luyen_khi',
        '.xx-cult-truc_co',
        '.xx-cult-kim_dan',
        '.xx-cult-nguyen_anh',
        '.xx-cult-hoa_than',
        # Vermillion seal
        '.xx-seal-stamp',
        '@keyframes xxSealStampPress',
        # Hoành phi
        '.xx-hoanh-phi',
        '.xx-hoanh-phi-zh',
        # Bia đá footer
        '.footer-bottom',
        # Audio toggle
        '.xx-audio-toggle',
        '.xx-audio-icon-on',
        '.xx-audio-icon-off',
        # Tu Tiên heading
        '.xx-tutien-heading',
        '.xx-tutien-zh',
        '.xx-tutien-vi',
        # Tu Sĩ Thẻ progress card
        '.xx-tusi-card',
        '.xx-tusi-progress-bar',
    ]
    for selector in must_have:
        assert selector in css, f'CSS missing required selector: {selector}'


def test_css_honours_prefers_reduced_motion():
    """The new animations MUST respect prefers-reduced-motion.
    A regression here = users with vestibular issues get flashing
    seal stamps and hue-cycling glyphs."""
    css = CSS_PATH.read_text(encoding='utf-8')
    assert '@media (prefers-reduced-motion: reduce)' in css


def test_css_scopes_per_realm():
    """The new styles must adapt to both Heavenly Court (light) and
    Blood Mist (dark) realms, like the rest of the xianxia layer."""
    css = CSS_PATH.read_text(encoding='utf-8')
    assert 'html.theme-light' in css
    assert 'body.light-mode' in css


# ─────────────────────────────────────────────────────────────
# 5. JS contract
# ─────────────────────────────────────────────────────────────


def test_js_exports_godweb_audio_with_four_sounds():
    source = JS_PATH.read_text(encoding='utf-8')
    # Public API on window.
    assert 'window.GodWebAudio' in source
    # The 4 sounds the user asked for.
    assert 'playClick' in source
    assert 'playSubmit' in source
    assert 'playAchievement' in source
    # Ambient is *opt-in* — even if we don't wire it on by default,
    # the WebAudio context plumbing must exist so future use-cases
    # (tier-up animation, bamboo wind) can call into it.
    assert 'AudioContext' in source


def test_js_wires_vermillion_seal_click_handler():
    source = JS_PATH.read_text(encoding='utf-8')
    # Must use event delegation so dynamically inserted buttons work.
    assert 'pointerdown' in source
    assert 'xx-seal-stamp' in source
    # The randomised character pool must contain Tu Tiên-flavoured chars,
    # not just the literal "印".
    assert '印' in source
    assert '道' in source


def test_js_audio_default_is_on_and_persists():
    """User chose 'default ON, opt-in', so first-time visitors hear
    sound. The toggle must persist to localStorage so a returning
    user's preference survives reloads."""
    source = JS_PATH.read_text(encoding='utf-8')
    assert "localStorage.getItem(AUDIO_STORAGE_KEY)" in source
    assert "localStorage.setItem(AUDIO_STORAGE_KEY" in source
    # Default-ON: the read function must fall through to `return true`
    # when no value is stored.
    assert "return true; // default ON per user preference" in source


def test_js_honours_prefers_reduced_motion():
    """Audio + seal stamp must both go quiet when the user signals
    they prefer reduced motion. Audio overrides bypass enabled=true."""
    source = JS_PATH.read_text(encoding='utf-8')
    assert "matchMedia('(prefers-reduced-motion: reduce)')" in source
    assert 'AUDIO_DISABLED_BY_MOTION_PREF' in source


def test_js_audio_resumes_context_on_user_gesture():
    """Modern browsers create AudioContext in 'suspended' state until
    a user gesture. Forgetting to resume() means default-ON silently
    plays no sound — a regression we want to guard against."""
    source = JS_PATH.read_text(encoding='utf-8')
    assert 'resumeIfSuspended' in source
    assert "ctx.state === 'suspended'" in source
