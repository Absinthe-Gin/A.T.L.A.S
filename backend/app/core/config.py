"""Centralised application configuration.

Every environment-dependent value is read here. No other module reads
environment variables directly.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogFormat(StrEnum):
    CONSOLE = "console"
    JSON = "json"


class LLMProviderName(StrEnum):
    OLLAMA = "ollama"
    # Deterministic stand-in that needs no external service.
    MOCK = "mock"


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Personal Assistant"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT

    # Address the development server listens on (`python -m app`).
    # Ports 8710/5710 are used instead of the common 8000/5173 so this
    # project does not collide with other projects on the same machine.
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8710, ge=1, le=65535)

    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # Comma-separated so the value stays a plain string in `.env`.
    cors_allowed_origins: str = "http://localhost:5710,http://127.0.0.1:5710"

    log_level: LogLevel = "INFO"
    log_format: LogFormat = LogFormat.CONSOLE

    # --- AI ---
    llm_provider: LLMProviderName = LLMProviderName.OLLAMA
    ollama_base_url: str = "http://localhost:11434"
    # Empty means "not configured": the app still starts, chat reports a clear error.
    ollama_model: str = ""
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    llm_timeout_seconds: float = Field(default=60.0, gt=0)
    # Upper bound on LLM round trips that request tools within one chat turn.
    ai_max_tool_iterations: int = Field(default=5, ge=1, le=20)
    ai_tool_timeout_seconds: float = Field(default=15.0, gt=0)
    # How many previous messages of the conversation are sent to the model.
    ai_context_max_messages: int = Field(default=20, ge=0, le=200)
    # How many long-term memories may be added to the context of one turn.
    ai_memory_limit: int = Field(default=5, ge=0, le=50)

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
