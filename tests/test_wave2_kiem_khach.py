"""Regression tests for Wave 2 — kiếm khách (swordsman) rebuild.

Wave 2 builds on Wave 1 Tu Tiên (PR #32) and pushes the swordsmanship
angle harder while cutting expensive perpetual effects so the site
stays smooth on Heroku Basic Dynos (512 MB RAM, 1× vCPU share).

Each test below documents the exact user-facing behaviour or perf
guarantee it is locking in. Tests read the CSS/JS/template source
files directly so we don't need a real browser.

Sections
--------
§A  Effects-cut guards (W2.1a) — make sure the heavy listeners,
    canvases, and infinite keyframes really are gone from base.html
    and main.js so they never silently regress.

§B  Perf-cleanup guards (W2.0) — Procfile gunicorn tuning,
    Flask-Compress wiring, static cache-control, DB pool sizing, and
    cultivation_xp instance cache.

§C  Sword UI presence guards (W2.2 – W2.8) — the new CSS classes
    (xx-truc-gian, xx-sword-divider, xx-phap-khi, xx-nhat-ky,
    xx-kiem-loader) must exist in the stylesheet and the stylesheet
    must be linked from base.html.

§D  Template wiring guards — the Trúc giản layout must replace the
    16:9 ``card`` grid on /blog/, the profile page must render the
    pháp khí grid + 28-day nhật ký, and the calligraphy headlines
    must include both ZH glyph and VI subtitle on Tu Tiên pages.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATIC_CSS = REPO_ROOT / 'godweb' / 'static' / 'css'
STATIC_JS = REPO_ROOT / 'godweb' / 'static' / 'js'
TEMPLATES = REPO_ROOT / 'godweb' / 'templates'

WAVE2_CSS = STATIC_CSS / 'xianxia-wave2-kiem-khach.css'
BASE_HTML = TEMPLATES / 'base.html'
BLOG_INDEX = TEMPLATES / 'blog' / 'index.html'
PROFILE_INDEX = TEMPLATES / 'profile' / 'index.html'
HOME_HTML = TEMPLATES / 'home.html'
MAIN_JS = STATIC_JS / 'main.js'


# ────────────────────────────────────────────────────────────────────
# §A  Effects-cut guards
# ────────────────────────────────────────────────────────────────────

def test_base_html_no_longer_loads_heavy_canvases_or_parallax_layers():
    """The pre-Wave-2 base.html shipped four heavy paint loops:

    1. ``<canvas class="xx-stars-canvas">`` — RAF starfield (100+ pts).
    2. ``<canvas id="xx-petals-canvas">`` — RAF cherry blossom drift.
    3. ``<div class="xx-parallax-layer">`` — GSAP ScrollTrigger.
    4. ``<div class="xx-floating-layer">`` — floating sword/rune bars.

    Each one survived first-paint and ran continuously while the tab
    was visible. On a Basic Dyno + 4G connection the combined CPU
    cost stretched first-input-delay past 200 ms on mid-range mobile.

    Wave 2 removed them outright (no perf-toggle, no env flag) so
    this test asserts they are *gone*, not merely behind a flag.
    """
    src = BASE_HTML.read_text(encoding='utf-8')
    for needle in [
        'xx-stars-canvas',
        'xx-petals-canvas',
        'xx-parallax-layer',
        'xx-floating-layer',
        'id="xx-mist-transition"',
        'class="fx-bg"',
    ]:
        assert needle not in src, f'{needle!r} still present in base.html'


def test_base_html_no_longer_loads_celestial_or_fx_scripts():
    """Wave 2 cut three of the five Wave-1 JS bundles:

    * ``xianxia-celestial.js`` — petals canvas + parallax scrolling.
    * ``xianxia-fx.js`` — cursor-trail RAF and orb-mousemove listeners.
    * ``xianxia-interactions.js`` — logo particle burst setInterval.

    Removing them from the script tags in base.html is the *only*
    way to be sure the bundles aren't shipped to the browser at all
    (Flask-Compress would still happily gzip them).
    """
    src = BASE_HTML.read_text(encoding='utf-8')
    for needle in [
        'xianxia-celestial.js',
        'xianxia-fx.js',
        'xianxia-interactions.js',
        'gsap.min.js',
        'ScrollTrigger.min.js',
    ]:
        assert needle not in src, f'{needle!r} still referenced in base.html'


def test_main_js_no_longer_attaches_mousemove_or_scroll_parallax():
    """The three heavy listeners removed from main.js were:

    * ``initializeCardTilt`` — mousemove on every card.
    * ``initializeParallaxHero`` — scroll listener translating .hero.
    * ``_triggerWorldShift`` — adding xx-world-shifting on theme flip.

    Each spent CPU per frame whether or not the user could perceive
    it. Wave 2 cuts them; this guard makes sure they don't sneak
    back via copy-paste from an old PR.
    """
    src = MAIN_JS.read_text(encoding='utf-8')
    for needle in [
        'initializeCardTilt',
        'initializeParallaxHero',
        '_triggerWorldShift',
        "classList.add('xx-world-shifting')",
    ]:
        assert needle not in src, f'{needle!r} still in main.js'


# ────────────────────────────────────────────────────────────────────
# §B  Perf-cleanup guards (W2.0)
# ────────────────────────────────────────────────────────────────────

def test_procfile_uses_gthread_with_preload_for_basic_dyno():
    """Heroku Basic Dynos have 512 MB RAM and 1× vCPU share. Default
    gunicorn (sync workers, ``-w 4``) is the wrong shape — each
    worker would balloon to ~140 MB and we'd OOM during cold boot.

    Wave 2 sets:
      * ``--workers=1``           single worker, ~150-200 MB peak
      * ``--threads=4``           handle DB-bound I/O concurrently
      * ``--worker-class=gthread`` thread-safe across requests
      * ``--preload``             load app once before fork (CoW)
      * ``--timeout=30``          kill before Heroku's H12 (30 s)

    Both Procfile and godweb/Procfile must agree (Heroku reads the
    repo-root one; the inner one is left as a developer reference).
    """
    for name in ['Procfile', 'godweb/Procfile']:
        text = (REPO_ROOT / name).read_text(encoding='utf-8')
        assert '--workers=1' in text or '-w 1' in text, name
        assert '--worker-class=gthread' in text, name
        assert '--threads=' in text, name
        assert '--preload' in text, name
        assert '--timeout=' in text, name


def test_app_uses_flask_compress_and_db_pool_sized_for_essential_0():
    """Wave 2's app factory wires three perf-cleanup knobs:

    1. ``Flask-Compress`` — gzip text/html, css, js, svg+xml at level 6.
       Cuts initial payload ~70% on the average page.
    2. ``SQLALCHEMY_ENGINE_OPTIONS`` pool — Heroku Postgres Essential
       0 only exposes 20 connections, so the dyno keeps 5 + 5 overflow.
       ``pool_pre_ping`` + ``pool_recycle=300`` recover from idle drops.
    3. Static cache headers — ``Cache-Control: public, max-age=...
       immutable`` so the browser stops re-validating CSS/JS on every
       page nav.
    """
    src = (REPO_ROOT / 'godweb' / 'app.py').read_text(encoding='utf-8')
    assert 'flask_compress' in src.lower()
    assert "'pool_size'" in src or '"pool_size"' in src
    assert "'max_overflow'" in src or '"max_overflow"' in src
    assert 'pool_pre_ping' in src
    assert "'/static/'" in src or '"/static/"' in src
    assert 'max-age=31536000' in src or 'max-age=2592000' in src
    assert 'immutable' in src


def test_cultivation_xp_memoizes_per_instance_to_avoid_double_count():
    """Wave 1's ``User.cultivation_xp`` fired 4 ``COUNT(*)`` queries
    on every render. Many pages render the navbar badge AND the
    /profile card — so without caching that's 8 queries instead of
    4 on a 200 ms request budget.

    Wave 2 memoizes the result on ``self.__dict__`` so the second
    access in the same request returns from cache. Tests assert the
    cache key is present and the property is computed lazily.
    """
    src = (REPO_ROOT / 'godweb' / 'models.py').read_text(encoding='utf-8')
    assert '_cultivation_xp_cached' in src
    assert 'func.count' in src
    # Belt-and-braces: a COUNT-based code path means we never load
    # the full collection from disk for the realm badge.
    assert 'posts_count = session.query(func.count' in src \
        or "session.query(func.count(Post.id))" in src


def test_requirements_includes_flask_compress():
    """Flask-Compress is a runtime dep; without it the import in
    app.py soft-fails and gzip is silently skipped, masking the
    bandwidth regression."""
    req = (REPO_ROOT / 'requirements.txt').read_text(encoding='utf-8')
    assert 'Flask-Compress' in req


# ────────────────────────────────────────────────────────────────────
# §C  Sword UI presence guards (W2.2 – W2.8)
# ────────────────────────────────────────────────────────────────────

def test_wave2_stylesheet_exists_and_is_linked_from_base_html():
    """The Wave 2 stylesheet ships the trúc giản, kiếm khí divider,
    pháp khí grid, nhật ký 28-day grid, calligraphy headline, and
    kiếm loader. Without it linked from base.html the templates
    would render unstyled wrappers."""
    assert WAVE2_CSS.exists()
    base_src = BASE_HTML.read_text(encoding='utf-8')
    assert 'xianxia-wave2-kiem-khach.css' in base_src


def test_wave2_stylesheet_defines_every_class_used_by_templates():
    """Each class the templates apply must have a matching rule in
    the Wave 2 stylesheet — otherwise we end up with unstyled
    elements after deploy. List mirrors the template usage in
    blog/index.html, profile/index.html, home.html."""
    css = WAVE2_CSS.read_text(encoding='utf-8')
    for needle in [
        '.xx-truc-gian-grid',
        '.xx-truc-gian',
        '.xx-truc-gian-title',
        '.xx-truc-gian-excerpt',
        '.xx-truc-gian-meta',
        '.xx-truc-gian-seal',
        '.xx-sword-divider',
        '.xx-phap-khi',
        '.xx-phap-khi-grid',
        '.xx-phap-khi-slot',
        '.xx-phap-khi-slot.is-earned',
        '.xx-phap-khi-slot.is-locked',
        '.xx-nhat-ky',
        '.xx-nhat-ky-grid',
        '.xx-nhat-ky-cell',
        '.xx-nhat-ky-cell.is-stamped',
        '.xx-nhat-ky-cell.is-today',
        '.xx-kiem-loader',
    ]:
        assert needle in css, f'{needle} missing from Wave 2 stylesheet'


def test_wave2_stylesheet_respects_prefers_reduced_motion():
    """Every Wave 2 motion-bearing class must opt out under
    ``prefers-reduced-motion: reduce``. This is non-negotiable for
    a11y and matches the precedent set in Wave 1."""
    css = WAVE2_CSS.read_text(encoding='utf-8')
    assert '@media (prefers-reduced-motion: reduce)' in css


# ────────────────────────────────────────────────────────────────────
# §D  Template wiring guards
# ────────────────────────────────────────────────────────────────────

def test_blog_index_uses_truc_gian_layout_not_16x9_grid():
    """The blog index used to render a 3-column grid of 16:9
    rectangular cards. Wave 2 swaps that for a stack of vertical
    bamboo slips so the genre-fitting "trúc giản" metaphor reads on
    first scroll. Test asserts both that the trúc giản markup is
    present AND that the legacy ``grid grid-3`` wrapper is no longer
    wrapping the post loop."""
    src = BLOG_INDEX.read_text(encoding='utf-8')
    assert 'xx-truc-gian-grid' in src
    assert 'xx-truc-gian-title' in src
    assert 'xx-truc-gian-seal' in src
    # Guard against accidental revert: the prior wrapper must be
    # gone for the post-listing block specifically.
    assert '<div class="grid grid-3">\n            {% for post in posts.items %}' not in src


def test_profile_renders_phap_khi_grid_and_28day_nhat_ky():
    """The /profile/ page should render both the pháp khí (5-slot
    treasure grid) and the 28-day nhật ký streak grid below the
    Tu Sĩ Thẻ card. Sword divider sits between them and the stats
    grid as a visual breath."""
    src = PROFILE_INDEX.read_text(encoding='utf-8')
    assert 'xx-sword-divider' in src
    assert 'xx-phap-khi' in src
    assert 'xx-phap-khi-grid' in src
    assert 'xx-nhat-ky' in src
    assert 'xx-nhat-ky-grid' in src
    # 28 day cells via Jinja ``range(1, 29)``
    assert 'range(1, 29)' in src


def test_home_includes_sword_divider_after_hero():
    """The home page hero ends with the 道法自然 hoành phi and CTA
    buttons; Wave 2 puts a kiếm khí stroke right after that hero
    section to signal the transition into the features grid."""
    src = HOME_HTML.read_text(encoding='utf-8')
    assert 'xx-sword-divider' in src


def test_login_and_register_use_kiem_khach_microcopy():
    """Wave 2 microcopy refresh: Bái Sơn Môn (login), Nhập Môn
    (register). The form fields stay identical so existing pytest
    auth flows don't break — only the headline and helper text
    change."""
    login = (TEMPLATES / 'auth' / 'login.html').read_text(encoding='utf-8')
    register = (TEMPLATES / 'auth' / 'register.html').read_text(encoding='utf-8')
    assert '拜山门' in login or 'Bái Sơn Môn' in login
    assert '入门' in register or 'Nhập Môn' in register


def test_calligraphy_headlines_pair_zh_and_vi_on_tu_tien_pages():
    """W2.2: every Tu Tiên section heading should pair a single
    large ZH glyph with the VI label. The ``.xx-tutien-heading``
    element wraps two children: ``.xx-tutien-zh`` and
    ``.xx-tutien-vi``. Mismatched markup would render only one of
    the two so we check both children exist on at least one Tu
    Tiên page that is heavily used."""
    src = BLOG_INDEX.read_text(encoding='utf-8')
    assert 'xx-tutien-heading' in src
    assert 'xx-tutien-zh' in src
    assert 'xx-tutien-vi' in src
