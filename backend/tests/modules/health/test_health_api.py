import httpx
import pytest
from sqlalchemy.exc import OperationalError

from app import __version__
from app.modules.health import service as health_service


async def test_health_returns_ok_when_database_is_reachable(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "testing",
        "version": __version__,
        "checks": {"database": "ok"},
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
    assert body["checks"] == {"database": "error"}


async def test_health_is_not_served_outside_the_versioned_prefix(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/health")

    assert response.status_code == 404
