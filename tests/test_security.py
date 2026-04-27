"""Regression tests for the security fixes shipped in this PR."""
from __future__ import annotations

import os

import pytest

from tests.conftest import extract_csrf_token


def test_secret_key_required_in_production(monkeypatch):
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('FLASK_ENV', 'production')
    from godweb.app import create_app
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app()


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
