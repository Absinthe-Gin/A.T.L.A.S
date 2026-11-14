"""The API returns one error envelope for every kind of failure."""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ExternalServiceTimeoutError,
    NotFoundError,
)
from app.main import create_app


class _Payload(BaseModel):
    amount: int = Field(gt=0)


class _ItemNotFoundError(NotFoundError):
    code = "item_not_found"
    message = "Không tìm thấy mục."


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """Client for an app that has extra routes which fail in known ways."""
    app: FastAPI = create_app(settings)

    @app.get("/test/not-found")
    async def raise_not_found() -> None:
        raise _ItemNotFoundError()

    @app.get("/test/conflict")
    async def raise_conflict() -> None:
        raise ConflictError("Mục đã tồn tại.")

    @app.get("/test/business-rule")
    async def raise_business_rule() -> None:
        raise BusinessRuleError(code="budget_exceeded")

    @app.get("/test/external-timeout")
    async def raise_external_timeout() -> None:
        raise ExternalServiceTimeoutError()

    @app.get("/test/unexpected")
    async def raise_unexpected() -> None:
        raise RuntimeError("secret internal detail")

    @app.post("/test/validate")
    async def validate(payload: _Payload) -> _Payload:
        return payload

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as http_client:
            yield http_client


@pytest.mark.parametrize(
    ("path", "status_code", "code", "message"),
    [
        ("/test/not-found", 404, "item_not_found", "Không tìm thấy mục."),
        ("/test/conflict", 409, "conflict", "Mục đã tồn tại."),
        (
            "/test/business-rule",
            422,
            "budget_exceeded",
            "Yêu cầu vi phạm quy tắc nghiệp vụ.",
        ),
        (
            "/test/external-timeout",
            504,
            "external_service_timeout",
            "Dịch vụ bên ngoài không phản hồi kịp thời.",
        ),
    ],
)
async def test_app_errors_use_the_error_envelope(
    client: httpx.AsyncClient, path: str, status_code: int, code: str, message: str
) -> None:
    response = await client.get(path)

    assert response.status_code == status_code
    error = response.json()["error"]
    assert error["code"] == code
    assert error["message"] == message
    assert error["details"] == []
    assert error["request_id"] == response.headers["X-Request-ID"]


async def test_unknown_route_uses_the_error_envelope(client: httpx.AsyncClient) -> None:
    response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_wrong_method_uses_the_error_envelope(client: httpx.AsyncClient) -> None:
    response = await client.delete("/test/not-found")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


async def test_invalid_request_body_lists_the_failing_fields(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/validate", json={"amount": 0})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert [detail["field"] for detail in error["details"]] == ["amount"]
    assert error["details"][0]["message"]


async def test_missing_request_field_is_reported(client: httpx.AsyncClient) -> None:
    response = await client.post("/test/validate", json={})

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "amount"


async def test_unexpected_error_returns_500_without_internal_details(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    response = await client.get("/test/unexpected")

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "internal_server_error"
    assert "secret internal detail" not in response.text
    assert error["request_id"] == response.headers["X-Request-ID"]

    # The cause is still available to developers through the log.
    logged = [record for record in caplog.records if record.message == "Unhandled exception"]
    assert len(logged) == 1
    assert logged[0].exc_info is not None
    assert "secret internal detail" in str(logged[0].exc_info[1])
