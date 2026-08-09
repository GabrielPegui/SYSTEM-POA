"""Application settings loaded from environment variables and .env files."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the application.

    Values can be provided through environment variables or a `.env` file
    located at the project root (see ``.env.example``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Purchase Order Automation API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    #: Namespaced to avoid collisions with the generic ``DEBUG`` variable that
    #: external tooling (e.g. Node's debug package, CI systems) sets in the host.
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = "INFO"

    #: Maximum accepted size (in megabytes) for an uploaded PDF document.
    max_upload_mb: int = 20

    database_url: str = Field(default="sqlite:///./poa_dev.db", validation_alias="DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()


settings = get_settings()
