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
    # Multiple `prefers-reduced-motion` queries can coexist (the perf
    # pass added one for aura animations) so we scan ALL of them and
    # require at least one to silence the world-shift overlay.
    assert 'prefers-reduced-motion' in source
    rm_idx = source.find('prefers-reduced-motion')
    while rm_idx != -1:
        block_end = source.find('}\n}', rm_idx)
        if block_end == -1:
            block_end = len(source)
        block = source[rm_idx:block_end]
        if 'xx-world-shifting' in block and 'animation: none' in block:
            return
        rm_idx = source.find('prefers-reduced-motion', rm_idx + 1)
    raise AssertionError(
        'No prefers-reduced-motion block disables the World Shift '
        'overlay animation'
    )


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


# ────────────────────────────────────────────────────────────────────
# 8. Aura overflow clipping — the rotating conic-gradient must not
#    bleed outside the card and read as red diagonal "ghosting" bars.
# ────────────────────────────────────────────────────────────────────
def test_immortal_card_clips_aura_via_overflow_hidden():
    """The rotating ``::before`` aura is a slightly oversized
    rectangle. If the parent ``.xx-immortal-card`` doesn't clip,
    rotation sweeps the rectangle's corners way past the card edge
    and they read as red diagonal bars around the post (the bug the
    user reported post-merge).

    The compound ``.card.xx-immortal-card`` selector is mandatory:
    it matches ``xianxia-theme.css``'s ``.card:has(.premium-badge)
    { overflow: visible }`` on specificity (0,2,0) and wins by load
    order. A plain ``.xx-immortal-card`` (0,1,0) would be silently
    overridden back to ``visible``.
    """
    source = CSS_PATH.read_text(encoding='utf-8')
    idx = source.find('.card.xx-immortal-card,\n.xx-immortal-card {')
    assert idx != -1, (
        'Immortal card block must use the compound selector to match '
        'legacy `.card:has(.premium-badge)` specificity'
    )
    # Walk to the matching closing brace.
    block_end = source.find('}', idx)
    block = source[idx:block_end + 1]
    assert 'overflow: hidden' in block, (
        '.card.xx-immortal-card needs `overflow: hidden` so the '
        'rotating ::before aura is clipped to the card boundary'
    )


def test_immortal_aura_spins_via_property_not_transform():
    """The original keyframe rotated the entire ``::before``
    pseudo-element. Because the card is non-square, the bounding
    box of the rotated rectangle extended past the card and was
    visible as red diagonal bars around each VIP post — even with
    the mask trick that carved a ring out of the rectangle.

    The fix is to keep the pseudo-element static and instead animate
    the conic-gradient's ``from <angle>`` parameter via a ``@property``
    custom property. The bounding box stays fixed; only the gradient
    spins inside it.
    """
    source = CSS_PATH.read_text(encoding='utf-8')
    assert "@property --xx-aura-spin" in source, (
        '@property --xx-aura-spin is required for the smooth conic '
        'angle animation that replaced the transform rotation'
    )
    # The xxImmortalAura keyframe must animate the angle, NOT
    # transform: rotate.
    kf_idx = source.find('@keyframes xxImmortalAura')
    assert kf_idx != -1
    kf_block = source[kf_idx:source.find('}', source.find('}', kf_idx) + 1) + 1]
    assert '--xx-aura-spin' in kf_block, (
        'xxImmortalAura must animate --xx-aura-spin (the conic-gradient '
        'angle), not transform: rotate (which causes bleed outside the card)'
    )
    assert 'transform: rotate' not in kf_block, (
        'xxImmortalAura keyframe must NOT animate transform: rotate — '
        'that was the source of the diagonal ghosting bars'
    )


def test_immortal_before_uses_from_var_aura_spin():
    """Both base and per-realm conic-gradient definitions must
    reference ``from var(--xx-aura-spin)`` so the @property animation
    actually drives them. A hard-coded ``from 0deg`` would render the
    aura static."""
    source = CSS_PATH.read_text(encoding='utf-8')
    # Find every `conic-gradient(` inside an `xx-immortal-card::before`
    # context. Easiest: scan the three known blocks.
    for marker in (
        '.xx-immortal-card::before {\n    content',  # base
        'html.theme-dark .xx-immortal-card::before {',  # dark realm
        'body.light-mode .xx-immortal-card::before {',  # light realm
    ):
        idx = source.find(marker)
        assert idx != -1, f'Expected ::before block missing: {marker!r}'
        block = source[idx:source.find('}', idx)]
        assert 'from var(--xx-aura-spin)' in block, (
            f'{marker!r} must use `from var(--xx-aura-spin)` so the '
            f'@property-driven keyframe spins the gradient instead of '
            f'rotating the whole pseudo-element'
        )


# ────────────────────────────────────────────────────────────────────
# 9. Performance — content-visibility, reduced-motion guards,
#    off-screen aura pausing via IntersectionObserver
# ────────────────────────────────────────────────────────────────────
def test_card_uses_content_visibility_auto():
    """The blog grid can hold dozens of `.card`s, each with a
    conic-gradient + filter on `::before`. `content-visibility: auto`
    lets the browser skip layout + paint for off-screen cards."""
    source = CSS_PATH.read_text(encoding='utf-8')
    idx = source.find('content-visibility: auto')
    assert idx != -1, (
        'Expected `content-visibility: auto` on .card / .post-card / '
        '.product-card so the browser can skip painting off-screen '
        'VIP auras'
    )
    # contain-intrinsic-size must accompany content-visibility, or
    # cards collapse to 0px and the layout jitters as the user scrolls.
    assert 'contain-intrinsic-size' in source


def test_reduced_motion_disables_immortal_aura_spin():
    """`prefers-reduced-motion: reduce` must silence the rotating
    aura and the pulse animations. The static colours still carry
    the realm identity; the spin is just decoration."""
    source = CSS_PATH.read_text(encoding='utf-8')
    # Find a reduced-motion block that targets the immortal aura.
    rm_idx = source.find('prefers-reduced-motion')
    assert rm_idx != -1
    # Scan forward — at least one reduced-motion block must mention
    # the immortal aura selector and set `animation: none`.
    while rm_idx != -1:
        block_end = source.find('}\n}', rm_idx)
        if block_end == -1:
            block_end = len(source)
        block = source[rm_idx:block_end]
        if 'xx-immortal-card' in block and 'animation: none' in block:
            return
        rm_idx = source.find('prefers-reduced-motion', rm_idx + 1)
    raise AssertionError(
        'No prefers-reduced-motion block disables the .xx-immortal-card '
        'aura animation — required for accessibility + perf on low-end '
        'devices'
    )


def test_main_js_pauses_off_screen_immortal_auras():
    """The CSS pauses aura when `.xx-aura-paused` is present.
    `main.js` must wire up an IntersectionObserver to toggle that
    class so off-screen cards stop driving the paint loop."""
    source = MAIN_JS_PATH.read_text(encoding='utf-8')
    assert 'initializeImmortalAuraVisibility' in source
    assert 'IntersectionObserver' in source
    # The class name in JS must match the CSS hook.
    assert 'xx-aura-paused' in source
    css = CSS_PATH.read_text(encoding='utf-8')
    assert 'xx-aura-paused' in css
    assert 'animation-play-state: paused' in css


def test_floating_clouds_skip_on_narrow_viewports():
    """The floating-cloud layer is purely decorative. Skipping it on
    mobile-sized viewports saves measurable GPU time (six blurred
    translucent layers) without hurting the brief's intent."""
    source = CELESTIAL_JS_PATH.read_text(encoding='utf-8')
    assert 'window.innerWidth < 640' in source, (
        'xianxia-celestial.js should bail out of cloud creation on '
        'narrow viewports'
    )


def test_petal_count_scales_with_viewport():
    """Cherry-blossom petal count should scale with viewport so a
    phone isn't paying the same per-frame compositing cost as a
    1440p monitor."""
    source = CELESTIAL_JS_PATH.read_text(encoding='utf-8')
    assert 'PETAL_COUNT' in source
    # The new logic uses Math.round(window.innerWidth / 100) clamped
    # to [6, 20]. We check the bounds + the scaling factor.
    assert 'window.innerWidth' in source
    assert 'Math.max(6' in source
    assert 'Math.min(20' in source
