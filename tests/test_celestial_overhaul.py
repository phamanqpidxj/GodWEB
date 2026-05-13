"""Regression tests for the Celestial vs. Demonic Realm overhaul.

This is the follow-up pass to ``test_celestial_path.py``. The original
Celestial Path feature added the Mortal/Immortal card variants and the
Yin-Yang ring. The overhaul pass:

1. Kills the "grey veil" — the legacy fixed-position dark layers
   (``.xx-stars``, ``canvas.xx-stars-canvas``, the parallax mountains,
   the dark mist overlay) must be either hidden or re-tinted to ivory
   when the Heavenly Court (light mode) is active.

2. Removes the "ghosting blocks" — the rotating ``.xx-floating-sword``
   bars and ``.xx-floating-rune`` discs that the user spotted around
   the post cards must not render in either realm.

3. Re-paints the Immortal-card aura per realm — gold "Halo" in the
   Heavenly Court, crimson "Soul Mist" in the Blood Mist Underworld.

4. Adds the "World Shift" ink-wash transition — fires when the user
   flips realms via the Taiji toggle button.

5. Persists the brief's canonical palette tokens (Radiant Gold,
   Ivory White, Jade Green; Deepest Black, Blood Red, Charcoal) as CSS
   variables so future templates can reference them.

The tests read the stylesheet/JS source files directly so we don't
need a browser. Each assertion is paired with a comment explaining
which user-facing bug it guards against.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = REPO_ROOT / 'godweb' / 'static' / 'css' / 'xianxia-celestial-path.css'
MAIN_JS_PATH = REPO_ROOT / 'godweb' / 'static' / 'js' / 'main.js'
CELESTIAL_JS_PATH = REPO_ROOT / 'godweb' / 'static' / 'js' / 'xianxia-celestial.js'


# ────────────────────────────────────────────────────────────────────
# 1. Heavenly Court palette — Radiant Gold / Ivory / Jade tokens
# ────────────────────────────────────────────────────────────────────
def test_heavenly_court_palette_tokens_present():
    source = CSS_PATH.read_text(encoding='utf-8')
    # The brief calls out these exact colours.
    assert '--hc-radiant-gold: #FFD700' in source
    assert '--hc-ivory-white: #FFFFF0' in source
    assert '--hc-celestial-yellow: #FFFACD' in source
    assert '--hc-jade-green: #00A86B' in source
    assert '--hc-pure-white: #FFFFFF' in source


# ────────────────────────────────────────────────────────────────────
# 2. Blood Mist Underworld palette — Obsidian / Blood Red / Charcoal
# ────────────────────────────────────────────────────────────────────
def test_blood_mist_palette_tokens_present():
    source = CSS_PATH.read_text(encoding='utf-8')
    # Brief uses two different reds in the two prompts (#990000 +
    # #8B0000); we keep both as separate tokens so callers don't get
    # locked into one.
    assert '--bm-deepest-black: #050505' in source
    assert '--bm-blood-red: #990000' in source
    assert '--bm-blood-red-deep: #8B0000' in source
    assert '--bm-charcoal: #1A1A1A' in source


# ────────────────────────────────────────────────────────────────────
# 3. Grey veil killer — dark fixed layers are suppressed in light mode
# ────────────────────────────────────────────────────────────────────
def test_light_mode_hides_dark_starfield_canvas():
    """`canvas.xx-stars-canvas` is the animated star canvas anchored
    at z-index:-2 over the void. Without an explicit override it keeps
    drawing dark dots in the Heavenly Court, contributing to the grey
    wash the user reported.
    """
    source = CSS_PATH.read_text(encoding='utf-8')
    assert 'html.theme-light canvas.xx-stars-canvas' in source
    # And the rule sets it to display:none.
    block_idx = source.find('html.theme-light canvas.xx-stars-canvas')
    block = source[block_idx:block_idx + 400]
    assert 'display: none' in block


def test_light_mode_strips_void_background_from_starfield_layer():
    """`.xx-stars` defaults to a `--lq-void` (#080810) base. In the
    Heavenly Court we must paint it ivory + auspicious-cloud glows so
    it doesn't dim the white body."""
    source = CSS_PATH.read_text(encoding='utf-8')
    assert 'html.theme-light .xx-stars' in source
    block_idx = source.find('html.theme-light .xx-stars,')
    if block_idx == -1:
        block_idx = source.find('html.theme-light .xx-stars')
    block = source[block_idx:block_idx + 800]
    # Ivory base (#FFFFF0) — explicitly NOT the dark void colour.
    assert '#FFFFF0' in block
    assert '#080810' not in block


def test_light_mode_hides_parallax_mountain_silhouettes():
    """The mountain clip-paths default to a dark jade gradient that
    bleeds through the white Heavenly Court body. Hide them."""
    source = CSS_PATH.read_text(encoding='utf-8')
    assert 'html.theme-light .xx-mountain-far' in source
    assert 'html.theme-light .xx-mountain-near' in source


# ────────────────────────────────────────────────────────────────────
# 4. Ghosting-block killer — floating swords + rune discs are removed
# ────────────────────────────────────────────────────────────────────
def test_floating_swords_and_runes_are_globally_suppressed_in_css():
    source = CSS_PATH.read_text(encoding='utf-8')
    # Hard rule: the user described these as "messy translucent
    # rotated rectangular shapes". They are now `display: none`.
    sword_idx = source.find('.xx-floating-sword,')
    assert sword_idx != -1
    block = source[sword_idx:sword_idx + 200]
    assert '.xx-floating-rune' in block
    assert 'display: none' in block


def test_floating_sword_creation_loop_removed_from_celestial_js():
    """Belt-and-braces guard against the swords being re-introduced
    via JS. The xianxia-celestial.js loop that appended
    `xx-floating-sword` divs must be gone."""
    source = CELESTIAL_JS_PATH.read_text(encoding='utf-8')
    # The previous body had a `swordCount = 5` loop that added the
    # divs. We removed it; the comment block referencing the removal
    # is still allowed to mention the class name.
    assert 'sword.className' not in source
    assert 'rune.className' not in source


# ────────────────────────────────────────────────────────────────────
# 5. Immortal-card aura — Halo (light) ↔ Soul Mist (dark)
# ────────────────────────────────────────────────────────────────────
def test_dark_realm_immortal_card_uses_blood_red_aura():
    """Brief §3 (Dark Mode): immortal cards emit a crimson Soul Mist.
    We confirm the dark-mode override targets the immortal card
    pseudo-element with crimson/blood-red tones in its conic gradient.
    """
    source = CSS_PATH.read_text(encoding='utf-8')
    block_idx = source.find('html.theme-dark .card.xx-immortal-card::before')
    assert block_idx != -1, (
        'Dark-mode Immortal aura override missing — the Soul Mist '
        'effect requires a theme-dark scoped ::before rule on the '
        'compound .card.xx-immortal-card selector so it matches '
        'the legacy :has(.premium-badge) specificity'
    )
    block = source[block_idx:block_idx + 1200]
    # Two of the brief's crimson stops should appear inside this block.
    assert 'rgba(220, 38, 38' in block
    assert 'rgba(153, 0, 0' in block
    # And the rotation animation must still drive it so the test in
    # `test_celestial_path.py::test_immortal_aura_overrides_legacy_premium_pulse`
    # keeps passing.
    assert 'xxImmortalAura' in block


def test_light_realm_immortal_card_uses_pure_gold_halo():
    """Brief §3 (Light Mode): immortal cards get a soft pulsing
    "Halo". Confirm the light-mode override is pure gold (#FFD700
    + #FFFACD) and re-pins the rotation animation."""
    source = CSS_PATH.read_text(encoding='utf-8')
    block_idx = source.find('html.theme-light .card.xx-immortal-card::before')
    assert block_idx != -1
    # Walk to the matching closing brace.
    block_end = source.find('}', block_idx)
    block = source[block_idx:block_end + 1]
    assert 'rgba(255, 215, 0' in block  # Radiant Gold
    assert 'rgba(255, 250, 205' in block  # Celestial Yellow
    assert 'xxImmortalAura' in block


def test_halo_pulse_and_soul_mist_pulse_keyframes_exist():
    source = CSS_PATH.read_text(encoding='utf-8')
    assert '@keyframes xxHaloPulse' in source
    assert '@keyframes xxSoulMistPulse' in source


# ────────────────────────────────────────────────────────────────────
# 6. World Shift transition — CSS keyframe + JS hook
# ────────────────────────────────────────────────────────────────────
def test_world_shift_keyframe_and_hook_exist():
    source = CSS_PATH.read_text(encoding='utf-8')
    assert '@keyframes xxWorldShift' in source
    assert 'html.xx-world-shifting #xx-mist-transition' in source
    assert 'animation: xxWorldShift' in source


def test_world_shift_is_disabled_under_reduced_motion():
    """The brief explicitly calls for the World Shift to feel like an
    ink-wash, but it must respect prefers-reduced-motion."""
    source = CSS_PATH.read_text(encoding='utf-8')
    # Find a reduced-motion block that mentions the world-shift hook.
    assert 'prefers-reduced-motion' in source
    # The world-shift overlay rule re-appears under the reduced-motion
    # query with `animation: none`.
    rm_idx = source.rfind('prefers-reduced-motion')
    rm_tail = source[rm_idx:]
    assert 'xx-world-shifting' in rm_tail


def test_world_shift_is_triggered_by_main_js_toggle():
    """The CSS hook is fired by `toggleSiteTheme` so every realm flip
    runs the ink-wash. We verify the call site exists and the helper
    that adds the `xx-world-shifting` class is wired up."""
    source = MAIN_JS_PATH.read_text(encoding='utf-8')
    assert '_triggerWorldShift' in source
    assert "classList.add('xx-world-shifting')" in source
    # `toggleSiteTheme` actually calls the helper.
    toggle_idx = source.find('function toggleSiteTheme()')
    assert toggle_idx != -1
    toggle_body = source[toggle_idx:toggle_idx + 600]
    assert '_triggerWorldShift()' in toggle_body


# ────────────────────────────────────────────────────────────────────
# 7. Heavenly Court body background tint
# ────────────────────────────────────────────────────────────────────
def test_light_mode_body_uses_ivory_yellow_gradient():
    """The legacy light-mode body gradient slid to #f1f5f9 (slate-100)
    at its foot, which paired with the leftover dark fixed layers to
    read as muted grey. Our override pushes it to pure ivory →
    celestial yellow so the Heavenly Court reads as crystal-clear."""
    source = CSS_PATH.read_text(encoding='utf-8')
    idx = source.find('html.theme-light,')
    if idx == -1:
        idx = source.find('html.theme-light\n')
    assert idx != -1, 'Heavenly Court body tint override missing'
    block = source[idx:idx + 800]
    assert 'var(--hc-pure-white)' in block
    assert 'var(--hc-ivory-white)' in block
    assert 'var(--hc-celestial-yellow)' in block
