from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import AppEnvironment, LLMProviderName, LogFormat, Settings
from app.main import create_app


def _settings(**values: object) -> Settings:
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_defaults_target_local_development(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "APP_ENV",
        "API_HOST",
        "API_PORT",
        "DATABASE_URL",
        "CORS_ALLOWED_ORIGINS",
        "LOG_LEVEL",
        "LOG_FORMAT",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = _settings()

    assert settings.app_env is AppEnvironment.DEVELOPMENT
    assert settings.database_url.startswith("sqlite+aiosqlite:///")
    assert settings.cors_origins == ["http://localhost:5710", "http://127.0.0.1:5710"]
    assert (settings.api_host, settings.api_port) == ("127.0.0.1", 8710)
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


def test_external_services_default_to_free_public_endpoints_without_a_key() -> None:
    settings = _settings()

    assert settings.nominatim_base_url == "https://nominatim.openstreetmap.org"
    assert settings.open_meteo_base_url == "https://api.open-meteo.com"
    assert settings.osrm_base_url == "https://router.project-osrm.org"
    assert settings.serpapi_api_key.get_secret_value() == ""
    assert settings.external_timeout_seconds > 0


def test_the_serpapi_key_is_never_shown_in_settings_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "s3cret")

    settings = _settings()

    assert settings.serpapi_api_key.get_secret_value() == "s3cret"
    assert "s3cret" not in repr(settings)


def test_external_timeout_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        _settings(external_timeout_seconds=0)


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


def test_ai_defaults_allow_starting_without_a_configured_model() -> None:
    settings = _settings()

    assert settings.llm_provider is LLMProviderName.OLLAMA
    assert settings.ollama_model == ""
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ai_max_tool_iterations == 5


def test_ai_settings_are_read_from_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("OLLAMA_MODEL", "some-model")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("AI_MAX_TOOL_ITERATIONS", "2")

    settings = _settings()

    assert settings.llm_provider is LLMProviderName.MOCK
    assert settings.ollama_model == "some-model"
    assert settings.llm_timeout_seconds == 12.5
    assert settings.ai_max_tool_iterations == 2


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("llm_provider", "openai"),
        ("api_port", 0),
        ("api_port", 70000),
        ("llm_temperature", -0.1),
        ("llm_temperature", 2.1),
        ("llm_timeout_seconds", 0),
        ("ai_max_tool_iterations", 0),
        ("ai_max_tool_iterations", 21),
        ("ai_tool_timeout_seconds", -1),
        ("ai_context_max_messages", -1),
        ("ai_memory_limit", 51),
    ],
)
def test_out_of_range_settings_are_rejected(name: str, value: object) -> None:
    with pytest.raises(ValidationError):
        _settings(**{name: value})


def test_overpass_defaults_to_the_public_endpoint_with_a_longer_timeout() -> None:
    settings = _settings()

    assert settings.overpass_base_url == "https://overpass-api.de/api/interpreter"
    assert settings.overpass_timeout_seconds == 30


def test_photon_is_the_second_provider_for_place_and_restaurant_search() -> None:
    assert _settings().photon_base_url == "https://photon.komoot.io"
