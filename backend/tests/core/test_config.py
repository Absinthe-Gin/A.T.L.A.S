from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import AppEnvironment, LogFormat, Settings
from app.main import create_app


def _settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_defaults_target_local_development(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("APP_ENV", "DATABASE_URL", "CORS_ALLOWED_ORIGINS", "LOG_LEVEL", "LOG_FORMAT"):
        monkeypatch.delenv(name, raising=False)

    settings = _settings()

    assert settings.app_env is AppEnvironment.DEVELOPMENT
    assert settings.database_url.startswith("sqlite+aiosqlite:///")
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.log_format is LogFormat.CONSOLE


def test_values_are_read_from_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./other.db")
    monkeypatch.setenv("LOG_FORMAT", "json")

    settings = _settings()

    assert settings.app_env is AppEnvironment.TESTING
    assert settings.database_url == "sqlite+aiosqlite:///./other.db"
    assert settings.log_format is LogFormat.JSON


def test_values_are_read_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=ERROR\nUNRELATED_KEY=ignored\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.log_level == "ERROR"


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = _settings(cors_allowed_origins=" http://a.test , http://b.test ,, ")

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


@pytest.mark.parametrize("value", ["verbose", "debug", ""])
def test_unknown_log_level_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        _settings(log_level=value)


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _settings(app_env="staging")


@pytest.mark.parametrize("origins", ["", "*", "https://app.example, *"])
def test_production_requires_explicit_cors_origins(origins: str) -> None:
    with pytest.raises(ValidationError, match="CORS_ALLOWED_ORIGINS"):
        _settings(app_env="production", cors_allowed_origins=origins)


def test_production_accepts_explicit_cors_origins() -> None:
    settings = _settings(app_env="production", cors_allowed_origins="https://app.example")

    assert settings.is_production
    assert settings.cors_origins == ["https://app.example"]


def test_api_docs_are_disabled_in_production(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'prod.db').as_posix()}"
    production = _settings(
        app_env="production",
        cors_allowed_origins="https://app.example",
        database_url=database_url,
    )
    development = _settings(app_env="development", database_url=database_url)

    assert create_app(production).docs_url is None
    assert create_app(production).openapi_url is None
    assert create_app(development).docs_url == "/docs"
