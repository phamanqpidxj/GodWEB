"""Tests for the site-wide login gate and the 7-day 'Remember me' cookie."""
from __future__ import annotations

from datetime import timedelta

from tests.conftest import extract_csrf_token


def _make_user(app, email='gate@example.com', password='pass-1234'):
    from godweb.extensions import db
    from godweb.models import User
    with app.app_context():
        user = User(
            username='gateuser',
            email=email,
            recovery_number='9999',
            godcoin_balance=0,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


def _login(client, email, password, remember=False):
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    data = {'email': email, 'password': password, 'csrf_token': token}
    if remember:
        data['remember'] = 'on'
    return client.post('/auth/login', data=data, follow_redirects=False)


def test_homepage_redirect_preserves_next(client):
    """The redirect to login must include ?next= so we land back on the original URL."""
    resp = client.get('/blog/?page=2', follow_redirects=False)
    assert resp.status_code == 302
    location = resp.headers['Location']
    assert '/auth/login' in location
    assert 'next=' in location


def test_logged_in_user_can_access_blog_and_store(app, client):
    _make_user(app)
    resp = _login(client, 'gate@example.com', 'pass-1234')
    assert resp.status_code == 302

    blog = client.get('/blog/')
    store = client.get('/store/')
    home = client.get('/')
    assert blog.status_code == 200
    assert store.status_code == 200
    assert home.status_code == 200


def test_remember_me_sets_long_lived_cookie(app, client):
    """Ticking 'remember' must produce a remember_token cookie with a future expiry (~7 days)."""
    _make_user(app)
    resp = _login(client, 'gate@example.com', 'pass-1234', remember=True)
    assert resp.status_code == 302

    set_cookie_headers = resp.headers.getlist('Set-Cookie')
    remember_cookies = [h for h in set_cookie_headers if h.startswith('remember_token=')]
    assert remember_cookies, f'remember_token cookie not set; headers={set_cookie_headers}'
    assert 'Expires=' in remember_cookies[0] or 'Max-Age=' in remember_cookies[0]

    # Verify config: REMEMBER_COOKIE_DURATION must be at least 7 days.
    assert app.config['REMEMBER_COOKIE_DURATION'] >= timedelta(days=7)
    assert app.config['PERMANENT_SESSION_LIFETIME'] >= timedelta(days=7)


def test_login_next_redirect_blocks_open_redirect(app, client):
    """The ?next= parameter must not allow off-site redirects."""
    _make_user(app)
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    resp = client.post(
        '/auth/login?next=https://evil.example.com/pwned',
        data={'email': 'gate@example.com', 'password': 'pass-1234', 'csrf_token': token},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    # Must NOT redirect to the attacker domain.
    assert 'evil.example.com' not in resp.headers['Location']


def test_uploads_route_is_gated(app, client):
    """File uploads (avatars, etc.) must not be accessible to anonymous visitors."""
    resp = client.get('/uploads/anything.png', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']
