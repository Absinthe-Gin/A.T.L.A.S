from pathlib import Path

import httpx
import pytest
from sqlalchemy.exc import OperationalError

from app import __version__
from app.core.config import LLMProviderName
from app.main import create_app
from app.modules.health import service as health_service
from tests.conftest import build_test_settings


async def test_health_returns_ok_when_database_is_reachable(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "testing",
        "version": __version__,
        "checks": {"database": "ok", "llm": {"status": "ok", "provider": "mock"}},
    }


async def test_health_returns_503_when_database_is_unreachable(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def failing_ping(_session: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("database is unavailable"))

    monkeypatch.setattr(health_service, "ping_database", failing_ping)

    response = await client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "error"


async def test_health_stays_ok_when_the_llm_service_is_not_running(database_path: Path) -> None:
    """The backend must start and report healthy without Ollama."""
    settings = build_test_settings(
        database_path,
        llm_provider=LLMProviderName.OLLAMA,
        # Port 9 (discard) is closed on a normal machine: the connection is refused.
        ollama_base_url="http://127.0.0.1:9",
        ollama_model="any-model",
    )
    app = create_app(settings)

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
            health = await http_client.get("/api/v1/health")
            chat = await http_client.post("/api/v1/chat", json={"message": "Xin chào"})

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["checks"]["llm"] == {"status": "unavailable", "provider": "ollama"}
    # Chat reports the outage through the standard error envelope.
    assert chat.status_code == 503
    assert chat.json()["error"]["code"] == "llm_unavailable"


async def test_health_is_not_served_outside_the_versioned_prefix(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/health")

    assert response.status_code == 404
