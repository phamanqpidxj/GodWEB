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
