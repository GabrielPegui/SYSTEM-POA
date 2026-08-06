"""Tests for application settings."""

from app.core.config import get_settings, settings


def test_settings_are_singleton() -> None:
    assert get_settings() is settings


def test_settings_defaults() -> None:
    assert settings.environment == "development"
    assert settings.api_prefix == "/api/v1"
    assert isinstance(settings.database_url, str)
