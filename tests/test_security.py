"""Regression tests for the security fixes shipped in this PR."""
from __future__ import annotations

from tests.conftest import extract_csrf_token


def test_secret_key_random_fallback_in_production(monkeypatch, caplog, tmp_path):
    """When SECRET_KEY is missing in prod we generate a random one + log a warning."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'fallback.db'}")
    fallback_secret = tmp_path / 'secret'
    monkeypatch.setenv('GODWEB_FALLBACK_SECRET_FILE', str(fallback_secret))
    import importlib
    import godweb.app as godweb_app
    importlib.reload(godweb_app)
    with caplog.at_level('WARNING', logger='godweb.app'):
        app = godweb_app.create_app()
    secret = app.config['SECRET_KEY']
    assert secret and len(secret) >= 32
    assert secret != godweb_app.DEFAULT_DEV_SECRET_KEY
    assert fallback_secret.exists()
    assert any('SECRET_KEY' in rec.message for rec in caplog.records), (
        'expected a loud warning when SECRET_KEY env var is missing'
    )


def test_secret_key_persisted_across_workers(monkeypatch, tmp_path):
    """Two create_app() calls (simulating two workers) share the same fallback key."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'shared.db'}")
    monkeypatch.setenv('GODWEB_FALLBACK_SECRET_FILE', str(tmp_path / 'shared-secret'))
    import importlib
    import godweb.app as godweb_app
    importlib.reload(godweb_app)
    app_a = godweb_app.create_app()
    app_b = godweb_app.create_app()
    assert app_a.config['SECRET_KEY'] == app_b.config['SECRET_KEY']


def test_no_default_admin_is_seeded(app):
    """Without ADMIN_EMAIL/ADMIN_PASSWORD env, no admin@godweb.com is created."""
    from godweb.models import User
    with app.app_context():
        assert User.query.filter_by(email='admin@godweb.com').first() is None


def test_admin_seed_via_env(monkeypatch, tmp_path):
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('ADMIN_EMAIL', 'owner@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'super-secret-pwd')
    monkeypatch.setenv('ADMIN_USERNAME', 'owner')
    db_path = tmp_path / 'admin-seed.db'
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{db_path}')

    from godweb.app import create_app
    app = create_app()
    from godweb.models import User
    with app.app_context():
        admin = User.query.filter_by(email='owner@example.com').first()
        assert admin is not None
        assert admin.role == 'admin'
        assert admin.check_password('super-secret-pwd')
        # Default admin email is NOT seeded as a side effect.
        assert User.query.filter_by(email='admin@godweb.com').first() is None


def test_post_without_csrf_is_rejected(client):
    response = client.post(
        '/auth/login',
        data={'email': 'x@x.com', 'password': 'x'},
        headers={'Origin': 'http://localhost', 'Referer': 'http://localhost/auth/login'},
    )
    assert response.status_code == 400


def test_cross_origin_post_is_rejected(client, csrf_token):
    response = client.post(
        '/auth/login',
        data={'email': 'x@x.com', 'password': 'x', 'csrf_token': csrf_token},
        headers={'Origin': 'https://evil.example.com'},
    )
    assert response.status_code == 403


def test_register_then_login_with_csrf(client):
    register_form = client.get('/auth/register').data.decode('utf-8')
    token = extract_csrf_token(register_form)

    response = client.post(
        '/auth/register',
        data={
            'username': 'alice',
            'email': 'alice@example.com',
            'recovery_number': '123456',
            'password': 'alice-pass',
            'confirm_password': 'alice-pass',
            'csrf_token': token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    login_form = client.get('/auth/login').data.decode('utf-8')
    token = extract_csrf_token(login_form)
    response = client.post(
        '/auth/login',
        data={'email': 'alice@example.com', 'password': 'alice-pass', 'csrf_token': token},
        follow_redirects=False,
    )
    assert response.status_code == 302
