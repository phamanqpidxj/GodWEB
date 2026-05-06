"""Tests for the admin-only Sentry debug routes."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import extract_csrf_token


def _seed_admin_and_user(app, *, admin_email='owner@example.com', admin_pw='admin-pass-1234',
                         user_email='regular@example.com', user_pw='user-pass-1234'):
    from godweb.extensions import db
    from godweb.models import User
    with app.app_context():
        admin = User(username='owner', email=admin_email, role='admin', recovery_number='9999')
        admin.set_password(admin_pw)
        regular = User(username='regular', email=user_email, recovery_number='1234')
        regular.set_password(user_pw)
        db.session.add_all([admin, regular])
        db.session.commit()


def _login(client, email, password):
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    return client.post(
        '/auth/login',
        data={'email': email, 'password': password, 'csrf_token': token},
        follow_redirects=False,
    )


def test_sentry_debug_message_is_admin_only(app, client):
    """Non-admin users must be redirected away from the debug routes."""
    _seed_admin_and_user(app)
    _login(client, 'regular@example.com', 'user-pass-1234')

    resp = client.get('/admin/sentry-debug/message', follow_redirects=False)
    assert resp.status_code == 302
    assert '/admin' not in resp.headers['Location'] or resp.headers['Location'] == '/'


def test_sentry_debug_error_is_admin_only(app, client):
    """Non-admins must NOT be able to crash the worker via the error route."""
    _seed_admin_and_user(app)
    _login(client, 'regular@example.com', 'user-pass-1234')

    resp = client.get('/admin/sentry-debug/error', follow_redirects=False)
    # Either redirected away by admin_required (302) or 401/403 -- but
    # crucially never a 500 because the route body must not have run.
    assert resp.status_code in (302, 401, 403)


def test_sentry_debug_message_reports_when_sdk_uninitialized(app, client):
    """Without SENTRY_DSN the route must flash a friendly error and redirect,
    not raise."""
    _seed_admin_and_user(app)
    _login(client, 'owner@example.com', 'admin-pass-1234')

    resp = client.get('/admin/sentry-debug/message', follow_redirects=True)
    assert resp.status_code == 200
    body = resp.data.decode('utf-8')
    assert 'Sentry chưa được khởi tạo' in body or 'sentry-sdk chưa' in body


def test_sentry_debug_message_captures_when_sdk_initialized(app, client):
    """Admin hitting the message route must call sentry_sdk.capture_message
    and flush the queue."""
    _seed_admin_and_user(app)
    _login(client, 'owner@example.com', 'admin-pass-1234')

    fake_client = object()  # truthy, stand-in for an initialized client

    class FakeHub:
        client = fake_client
        current = None  # set below

    FakeHub.current = FakeHub

    with patch('sentry_sdk.Hub', FakeHub), \
         patch('sentry_sdk.capture_message', return_value='abc123') as cap, \
         patch('sentry_sdk.flush') as flush:
        resp = client.get('/admin/sentry-debug/message', follow_redirects=True)

    assert resp.status_code == 200
    cap.assert_called_once()
    flush.assert_called_once()
    assert 'abc123' in resp.data.decode('utf-8')


def test_sentry_debug_error_raises_for_admin(app, client):
    """The error route must propagate the exception so Sentry's WSGI
    integration captures it. The Flask test client surfaces this as a 500."""
    _seed_admin_and_user(app)
    _login(client, 'owner@example.com', 'admin-pass-1234')

    app.config['PROPAGATE_EXCEPTIONS'] = False
    resp = client.get('/admin/sentry-debug/error')
    assert resp.status_code == 500
