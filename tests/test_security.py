"""Regression tests for the security fixes shipped in this PR."""
from __future__ import annotations

from tests.conftest import extract_csrf_token


def test_secret_key_persisted_in_db_in_production(monkeypatch, tmp_path):
    """When SECRET_KEY is missing in prod we persist a random one in the DB."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    db_path = tmp_path / 'fallback.db'
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    monkeypatch.setenv('GODWEB_FALLBACK_SECRET_FILE', str(tmp_path / 'secret'))
    import importlib
    import godweb.app as godweb_app
    importlib.reload(godweb_app)
    app = godweb_app.create_app()
    secret = app.config['SECRET_KEY']
    assert secret and len(secret) >= 32
    assert secret != godweb_app.DEFAULT_DEV_SECRET_KEY

    # The DB row must hold the same secret so future workers / dyno restarts
    # reuse it instead of generating a new one.
    import sqlite3
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            "SELECT value FROM app_secrets WHERE key = 'session_secret'"
        ).fetchone()
    assert row is not None
    assert row[0] == secret


def test_secret_key_persisted_across_workers(monkeypatch, tmp_path):
    """Two create_app() calls (simulating two workers) share the same DB-backed key."""
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


def test_secret_key_survives_simulated_dyno_restart(monkeypatch, tmp_path):
    """Even after the local filesystem is wiped, the DB-backed secret stays the same."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    db_path = tmp_path / 'survive.db'
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    fallback = tmp_path / 'fallback'
    monkeypatch.setenv('GODWEB_FALLBACK_SECRET_FILE', str(fallback))

    import importlib
    import godweb.app as godweb_app
    importlib.reload(godweb_app)
    app1 = godweb_app.create_app()
    secret1 = app1.config['SECRET_KEY']

    # Simulate dyno restart wiping ephemeral files (but DB persists).
    if fallback.exists():
        fallback.unlink()
    importlib.reload(godweb_app)
    app2 = godweb_app.create_app()
    assert app2.config['SECRET_KEY'] == secret1


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
