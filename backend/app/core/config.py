"""Centralised application configuration.

Every environment-dependent value is read here. No other module reads
environment variables directly.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogFormat(StrEnum):
    CONSOLE = "console"
    JSON = "json"


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Personal Assistant"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT

    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # Comma-separated so the value stays a plain string in `.env`.
    cors_allowed_origins: str = "http://localhost:5173"

    log_level: LogLevel = "INFO"
    log_format: LogFormat = LogFormat.CONSOLE

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env is AppEnvironment.PRODUCTION

    @model_validator(mode="after")
    def _validate_production_cors(self) -> Self:
        if not self.is_production:
            return self
        origins = self.cors_origins
        if not origins or "*" in origins:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS must list explicit origins when APP_ENV=production."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once from the environment."""
    return Settings()
