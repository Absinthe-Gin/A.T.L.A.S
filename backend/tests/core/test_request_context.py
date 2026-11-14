"""Request ID propagation and CORS behaviour."""

import httpx
import pytest

from app.core.request_context import get_request_id


async def test_response_carries_a_generated_request_id(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 32
    assert request_id.isalnum()


async def test_each_request_gets_a_different_request_id(client: httpx.AsyncClient) -> None:
    first = await client.get("/api/v1/health")
    second = await client.get("/api/v1/health")

    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


async def test_valid_client_request_id_is_reused(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "client-trace-123"})

    assert response.headers["X-Request-ID"] == "client-trace-123"


@pytest.mark.parametrize("unsafe", ["has space", "x" * 65, 'quote"injection', "line\tbreak"])
async def test_unsafe_client_request_id_is_replaced(client: httpx.AsyncClient, unsafe: str) -> None:
    response = await client.get("/api/v1/health", headers={"X-Request-ID": unsafe})

    assert response.headers["X-Request-ID"] != unsafe


async def test_request_id_is_logged_with_the_access_log(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    response = await client.get("/api/v1/health")

    access = [record for record in caplog.records if record.message == "Request completed"]
    assert len(access) == 1
    assert access[0].__dict__["status_code"] == 200
    assert access[0].__dict__["path"] == "/api/v1/health"
    assert access[0].__dict__["method"] == "GET"
    assert response.headers["X-Request-ID"]


async def test_request_id_does_not_leak_outside_the_request(client: httpx.AsyncClient) -> None:
    await client.get("/api/v1/health")

    assert get_request_id() is None


async def test_allowed_origin_receives_cors_headers(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]


async def test_unknown_origin_receives_no_cors_headers(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/health", headers={"Origin": "http://evil.example"})

    assert "access-control-allow-origin" not in response.headers


async def test_error_response_keeps_cors_headers(client: httpx.AsyncClient) -> None:
    response = await client.get("/missing", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 404
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
