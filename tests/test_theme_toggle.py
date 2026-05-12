"""Tests for the light/dark theme toggle.

Verifies the three invariants that FEAT-001 established:

1. The inline anti-flash script lives inside ``<head>`` and physically before
   ``<body>`` in the rendered HTML. If it ever leaks back into ``<body>`` (as
   it used to) browsers would paint a white flash on every page load.
2. The toggle button contains both a moon SVG and a sun SVG as direct DOM
   children. CSS alone decides which one is visible, so the old
   ``innerHTML``-swap race (which could render a Font Awesome gear if the
   stylesheet had not parsed yet) cannot happen again.
3. The theme toggle element never renders a Font Awesome gear: ``fa-cog`` /
   ``fa-gear`` must not appear inside the ``#toggleSiteTheme`` button.
4. The localStorage key ``'siteTheme'`` is referenced in the head script so
   users who already opted into light mode stay opted in.
"""
from __future__ import annotations

import re


def _rendered_login_html(client) -> str:
    response = client.get('/auth/login')
    assert response.status_code == 200
    return response.data.decode('utf-8')


def test_anti_flash_script_lives_inside_head(client):
    html = _rendered_login_html(client)

    head_close = html.find('</head>')
    # Look for the actual opening tag, not the literal substring '<body'
    # which can appear inside the anti-flash script comment itself.
    body_match = re.search(r'<body\s+class=', html)
    assert head_close != -1, 'missing </head>'
    assert body_match is not None, 'missing <body>'
    body_open = body_match.start()
    assert head_close < body_open, '<body> must come after </head>'

    # The anti-flash script references the localStorage key 'siteTheme' so
    # we can locate it unambiguously.
    theme_ref = html.find("localStorage.getItem('siteTheme')")
    assert theme_ref != -1, 'anti-flash script not found at all'
    assert theme_ref < head_close, (
        'anti-flash script must be inside <head> so it runs before the '
        'browser paints <body>. Found it at byte %d but </head> is at %d.'
        % (theme_ref, head_close)
    )


def test_toggle_button_contains_both_svg_icons(client):
    html = _rendered_login_html(client)

    btn_match = re.search(
        r'<button[^>]*id="toggleSiteTheme"[^>]*>(.*?)</button>',
        html,
        re.DOTALL,
    )
    assert btn_match, '#toggleSiteTheme button not rendered'
    btn_inner = btn_match.group(1)

    assert 'class="theme-icon-moon"' in btn_inner, (
        'moon SVG wrapper missing from toggle button'
    )
    assert 'class="theme-icon-sun"' in btn_inner, (
        'sun SVG wrapper missing from toggle button'
    )
    assert btn_inner.count('<svg') >= 2, 'expected two inline <svg> icons'


def test_toggle_button_never_shows_a_gear(client):
    html = _rendered_login_html(client)

    btn_match = re.search(
        r'<button[^>]*id="toggleSiteTheme"[^>]*>(.*?)</button>',
        html,
        re.DOTALL,
    )
    assert btn_match
    btn_inner = btn_match.group(1)
    assert 'fa-cog' not in btn_inner, 'theme toggle must not render a gear icon'
    assert 'fa-gear' not in btn_inner, 'theme toggle must not render a gear icon'

    mobile_match = re.search(
        r'<a[^>]*id="mobileThemeToggle"[^>]*>(.*?)</a>',
        html,
        re.DOTALL,
    )
    assert mobile_match, '#mobileThemeToggle link not rendered'
    mobile_inner = mobile_match.group(1)
    assert 'fa-cog' not in mobile_inner
    assert 'fa-gear' not in mobile_inner
    assert 'class="theme-icon-moon"' in mobile_inner
    assert 'class="theme-icon-sun"' in mobile_inner


def test_localstorage_key_name_is_preserved(client):
    """The key name 'siteTheme' must not change - users already have it set
    in their browsers and we do not want to silently reset their preference.
    """
    html = _rendered_login_html(client)
    head_html = html[: html.find('</head>')]
    assert "'siteTheme'" in head_html, (
        "anti-flash script must reference localStorage key 'siteTheme'"
    )


def test_body_light_mode_mirror_runs_before_descendants(client):
    """A second inline script at the top of <body> mirrors the theme-light
    state onto body.classList so the many body.light-mode CSS rules match
    on the FIRST frame for returning light-mode users. This must live
    between the opening <body> tag and the first body descendant, otherwise
    the DOMContentLoaded hop it replaces reintroduces a dark-flash FOUC.
    """
    html = _rendered_login_html(client)

    body_open_match = re.search(r'<body\s+class="[^"]*">', html)
    assert body_open_match, 'missing <body>'
    body_open_end = body_open_match.end()

    # The mirror script touches body.classList and references 'light-mode'.
    mirror_idx = html.find("document.body.classList.add('light-mode')")
    assert mirror_idx != -1, (
        'body-level light-mode mirror script missing from base.html'
    )
    assert mirror_idx > body_open_end, (
        'mirror script must live inside <body>, not <head>'
    )

    # Nothing other than whitespace/script tags should come between the
    # opening <body> tag and the mirror script - if a descendant element
    # were rendered first, it would paint with the wrong theme class.
    between = html[body_open_end:mirror_idx]
    # Allow only whitespace + the opening <script> tag and its preamble.
    assert '<div' not in between.lower(), (
        'mirror script must run before the first <div> descendant'
    )
    assert '<nav' not in between.lower(), (
        'mirror script must run before <nav>'
    )


def test_initial_aria_label_describes_next_action(client):
    """Before DOMContentLoaded, the toggle's inline aria-label is the only
    accessible name a screen-reader user hears. The dark theme is the
    default, so the name should describe the next action ("switch to
    light mode") rather than a generic "change appearance" string.
    """
    html = _rendered_login_html(client)

    btn_match = re.search(
        r'<button[^>]*id="toggleSiteTheme"[^>]*>',
        html,
    )
    assert btn_match, '#toggleSiteTheme not rendered'
    open_tag = btn_match.group(0)
    assert 'aria-label="Chuy\u1ec3n sang ch\u1ebf \u0111\u1ed9 s\u00e1ng"' in open_tag, (
        'desktop toggle should advertise the next action before JS runs'
    )

    mobile_match = re.search(
        r'<a[^>]*id="mobileThemeToggle"[^>]*>',
        html,
    )
    assert mobile_match, '#mobileThemeToggle not rendered'
    mobile_open = mobile_match.group(0)
    assert 'aria-label="Chuy\u1ec3n sang ch\u1ebf \u0111\u1ed9 s\u00e1ng"' in mobile_open, (
        'mobile toggle should advertise the next action before JS runs'
    )


def test_main_js_preserves_theme_toggle_contract():
    """Pytest-only regression guard for the JS contract in main.js.

    Rather than introducing a Node toolchain (JSDOM/Playwright) just to
    exercise four lines of script, we read ``main.js`` as source text and
    assert the key contract lines are present. If ``toggleSiteTheme`` were
    silently gutted or someone swapped the persistence key / root-class
    name, this test would catch it.
    """
    from pathlib import Path

    main_js = Path(__file__).resolve().parent.parent / 'godweb' / 'static' / 'js' / 'main.js'
    source = main_js.read_text(encoding='utf-8')

    # Persistence line: value is written to localStorage under the
    # existing 'siteTheme' key (single-quoted form as in current main.js).
    assert "localStorage.setItem('siteTheme'" in source, (
        "main.js must persist the theme choice under the 'siteTheme' key"
    )

    # Root-class toggle: <html> carries theme-light / theme-dark.
    assert "classList.toggle('theme-light'" in source, (
        "main.js must toggle the 'theme-light' class on <html>"
    )

    # Body-class mirror: the legacy body.light-mode selectors depend on
    # this. The previous revision pass removed the html-level light-mode
    # toggle, but the body mirror must stay.
    assert "classList.toggle('light-mode'" in source, (
        "main.js must mirror the light state onto body.classList as "
        "'light-mode' for the legacy body.light-mode CSS selectors"
    )

    # Click wiring: toggleSiteTheme must be attached as a click listener
    # so the button actually does anything.
    assert "addEventListener('click', toggleSiteTheme)" in source, (
        "main.js must attach toggleSiteTheme as a click listener"
    )

