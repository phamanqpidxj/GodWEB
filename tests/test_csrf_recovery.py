"""Regression tests for the post-deployment CSRF recovery flow.

After a SECRET_KEY rotation (e.g. moving from a /tmp fallback to the
DB-backed key in PR #4), browsers carry a stale ``session`` cookie that
the new key can't deserialize. The form's CSRF token then has nothing
to validate against and Flask-WTF raises CSRFError -> a bare 400 page.

The custom CSRF handler must:
  - clear the stale session,
  - flash a friendly message,
  - bounce the user back to the login form so a fresh session + token
    are issued automatically.
"""
from __future__ import annotations

from tests.conftest import extract_csrf_token


def _seed_user(app, email='csrf@example.com', password='pass-1234'):
    from godweb.extensions import db
    from godweb.models import User
    with app.app_context():
        user = User(
            username='csrfuser',
            email=email,
            recovery_number='9999',
            godcoin_balance=0,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


def test_post_with_stale_session_redirects_to_login(client):
    """Submitting the login form after the session cookie was wiped must
    redirect (302) to /auth/login, not return a bare 400."""
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))

    # Simulate a stale/missing session cookie (what happens to real users
    # right after SECRET_KEY rotation).
    with client.session_transaction() as sess:
        sess.clear()

    resp = client.post(
        '/auth/login',
        data={'csrf_token': token, 'email': 'csrf@example.com',
              'password': 'pass-1234'},
        follow_redirects=False,
    )

    assert resp.status_code == 302, (
        f'Expected redirect, got {resp.status_code}: {resp.data[:200]!r}'
    )
    assert resp.headers['Location'].endswith('/auth/login')


def test_csrf_recovery_shows_friendly_message_and_works_on_retry(app, client):
    """After the recovery redirect the user must see a friendly flash
    and be able to log in normally on the next attempt."""
    _seed_user(app)

    # First attempt with stale session
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    with client.session_transaction() as sess:
        sess.clear()
    resp = client.post(
        '/auth/login',
        data={'csrf_token': token, 'email': 'csrf@example.com',
              'password': 'pass-1234'},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')
    assert 'hết hạn' in body, f'Friendly flash message missing: {body[:300]!r}'

    # Retry with a fresh CSRF token (same client/session)
    token2 = extract_csrf_token(body)
    resp2 = client.post(
        '/auth/login',
        data={'csrf_token': token2, 'email': 'csrf@example.com',
              'password': 'pass-1234'},
        follow_redirects=False,
    )
    assert resp2.status_code == 302, resp2.data[:200]
    assert resp2.headers['Location'] == '/'


def test_csrf_recovery_preserves_safe_next(client):
    """If ?next= is a same-origin relative path it must survive the
    CSRF-recovery bounce so users return to where they came from."""
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    with client.session_transaction() as sess:
        sess.clear()

    resp = client.post(
        '/auth/login?next=/blog/',
        data={'csrf_token': token, 'email': 'csrf@example.com',
              'password': 'pass-1234'},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers['Location'] == '/auth/login?next=/blog/'


def test_csrf_recovery_drops_open_redirect_next(client):
    """Absolute or protocol-relative ``next`` values must be discarded
    by the recovery handler (open-redirect guard)."""
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    with client.session_transaction() as sess:
        sess.clear()

    for evil in ('https://evil.example.com/x', '//evil.example.com/x'):
        resp = client.post(
            f'/auth/login?next={evil}',
            data={'csrf_token': token, 'email': 'csrf@example.com',
                  'password': 'pass-1234'},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert 'evil.example.com' not in resp.headers['Location']
        assert resp.headers['Location'] == '/auth/login'


def test_gate_redirect_uses_relative_next(client):
    """The site-wide login gate must produce ?next=<relative path>
    (not an absolute URL) so the login route's open-redirect guard
    actually honors it after a successful login."""
    resp = client.get('/blog/?page=2', follow_redirects=False)
    assert resp.status_code == 302
    location = resp.headers['Location']
    assert location.startswith('/auth/login?next=/blog/'), location
    assert 'http' not in location.split('next=', 1)[1]
