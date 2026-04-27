"""Shared pytest fixtures for the GodWeb test-suite."""
from __future__ import annotations

import os
import re
import tempfile

import pytest


def _build_app():
    # Lazy import so each test process can configure env first.
    from godweb.app import create_app
    return create_app()


@pytest.fixture()
def app(monkeypatch, tmp_path):
    monkeypatch.delenv('FLASK_ENV', raising=False)
    monkeypatch.delenv('DYNO', raising=False)
    monkeypatch.delenv('ADMIN_EMAIL', raising=False)
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')

    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{db_path}')

    upload_dir = tmp_path / 'uploads'
    upload_dir.mkdir()

    app = _build_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=True,
        UPLOAD_FOLDER=str(upload_dir),
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def extract_csrf_token(html: str) -> str:
    """Pull the csrf_token value out of a rendered form."""
    match = re.search(
        r'name="csrf_token"\s+value="([^"]+)"',
        html,
    )
    assert match, 'CSRF token not found in response body'
    return match.group(1)


@pytest.fixture()
def csrf_token(client):
    """Fetch a fresh CSRF token by hitting the login form."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    return extract_csrf_token(response.data.decode('utf-8'))
