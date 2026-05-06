"""Tests for the Sentry error-reporting wiring.

The integration is gated on the ``SENTRY_DSN`` environment variable so
local dev and the test-suite never talk to Sentry. When the DSN is set
we initialize ``sentry_sdk`` with the Flask + SQLAlchemy integrations
and tag the event with the Heroku release if available.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture()
def clean_env(monkeypatch, tmp_path):
    """Provide the minimum env that ``create_app`` needs and nothing else."""
    monkeypatch.delenv('FLASK_ENV', raising=False)
    monkeypatch.delenv('DYNO', raising=False)
    monkeypatch.delenv('ADMIN_EMAIL', raising=False)
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)
    monkeypatch.delenv('SENTRY_DSN', raising=False)
    monkeypatch.delenv('SENTRY_RELEASE', raising=False)
    monkeypatch.delenv('SENTRY_ENVIRONMENT', raising=False)
    monkeypatch.delenv('HEROKU_SLUG_COMMIT', raising=False)
    monkeypatch.delenv('HEROKU_RELEASE_VERSION', raising=False)

    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    db_path = tmp_path / 'sentry.db'
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{db_path}')
    yield


def test_sentry_not_initialized_without_dsn(clean_env):
    """No DSN -> sentry_sdk.init must NOT be called."""
    with patch('sentry_sdk.init') as mock_init:
        from godweb.app import create_app
        create_app()
    mock_init.assert_not_called()


def test_sentry_initialized_when_dsn_present(clean_env, monkeypatch):
    """DSN present -> sentry_sdk.init is called with Flask + SQLAlchemy
    integrations, sane defaults, and PII disabled."""
    monkeypatch.setenv('SENTRY_DSN', 'https://example@o0.ingest.sentry.io/0')
    monkeypatch.setenv('HEROKU_SLUG_COMMIT', 'abc1234')

    with patch('sentry_sdk.init') as mock_init:
        from godweb.app import create_app
        create_app()

    assert mock_init.called, 'sentry_sdk.init was not called'
    kwargs = mock_init.call_args.kwargs
    assert kwargs['dsn'] == 'https://example@o0.ingest.sentry.io/0'
    assert kwargs['environment'] == 'development'
    assert kwargs['release'] == 'abc1234'
    assert kwargs['send_default_pii'] is False
    assert 0.0 <= kwargs['traces_sample_rate'] <= 1.0
    assert 0.0 <= kwargs['profiles_sample_rate'] <= 1.0

    integration_names = {type(i).__name__ for i in kwargs['integrations']}
    assert 'FlaskIntegration' in integration_names
    assert 'SqlalchemyIntegration' in integration_names


def test_sentry_environment_defaults_to_production_on_heroku(clean_env, monkeypatch):
    """When DYNO is set we tag the environment as 'production' by default."""
    monkeypatch.setenv('SENTRY_DSN', 'https://example@o0.ingest.sentry.io/0')
    monkeypatch.setenv('DYNO', 'web.1')

    with patch('sentry_sdk.init') as mock_init:
        from godweb.app import create_app
        create_app()

    assert mock_init.call_args.kwargs['environment'] == 'production'


def test_sentry_sample_rates_clamped(clean_env, monkeypatch):
    """Out-of-range or non-numeric sample rates fall back to safe values."""
    monkeypatch.setenv('SENTRY_DSN', 'https://example@o0.ingest.sentry.io/0')
    monkeypatch.setenv('SENTRY_TRACES_SAMPLE_RATE', '99')
    monkeypatch.setenv('SENTRY_PROFILES_SAMPLE_RATE', 'not-a-number')

    with patch('sentry_sdk.init') as mock_init:
        from godweb.app import create_app
        create_app()

    kwargs = mock_init.call_args.kwargs
    assert kwargs['traces_sample_rate'] == 1.0  # 99 clamped to 1.0
    assert kwargs['profiles_sample_rate'] == 0.0  # invalid -> default 0.0
