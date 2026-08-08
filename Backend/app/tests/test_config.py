"""Tests for application settings."""

import pytest

from app.core.config import Settings, get_settings, settings


def test_settings_are_singleton() -> None:
    assert get_settings() is settings


def test_settings_defaults() -> None:
    assert settings.environment == "development"
    assert isinstance(settings.database_url, str)


def test_debug_defaults_to_false() -> None:
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("APP_DEBUG", raising=False)
        assert Settings().debug is False


def test_debug_reads_namespaced_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_DEBUG", "true")
    assert Settings().debug is True
    monkeypatch.setenv("APP_DEBUG", "false")
    assert Settings().debug is False


def test_generic_debug_env_var_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """External tooling sets ``DEBUG`` in the host; it must not break parsing.

    Regression for the ``DEBUG=release`` validation crash.
    """
    monkeypatch.setenv("DEBUG", "release")
    monkeypatch.setenv("APP_DEBUG", "false")
    assert Settings().debug is False
