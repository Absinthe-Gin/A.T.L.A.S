"""Convert exceptions into the single error envelope used by the API."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError, ErrorDetail
from app.core.request_context import get_request_id

logger = logging.getLogger(__name__)

_HTTP_ERROR_CODES: dict[int, str] = {
    400: "bad_request",
    404: "not_found",
    405: "method_not_allowed",
}

INTERNAL_ERROR_CODE = "internal_server_error"
INTERNAL_ERROR_MESSAGE = "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def build_error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or [],
            request_id=get_request_id(),
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def build_internal_error_response() -> JSONResponse:
    """Response for unexpected failures. Never exposes internal details."""
    return build_error_response(500, INTERNAL_ERROR_CODE, INTERNAL_ERROR_MESSAGE)


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    logger.log(
        exc.log_level,
        "Request failed: %s",
        exc.message,
        extra={
            "error_code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
        exc_info=exc if exc.status_code >= 500 else None,
    )
    return build_error_response(exc.status_code, exc.code, exc.message, exc.details)


async def _handle_request_validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ErrorDetail(
            # The first location item is the request part (body, query, path).
            field=".".join(str(part) for part in error["loc"][1:]) or None,
            message=str(error["msg"]),
        )
        for error in exc.errors()
    ]
    logger.info(
        "Request validation failed",
        extra={"path": request.url.path, "error_count": len(details)},
    )
    return build_error_response(422, "validation_error", "Dữ liệu yêu cầu không hợp lệ.", details)


async def _handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_ERROR_CODES.get(exc.status_code, f"http_{exc.status_code}")
    logger.info(
        "HTTP error",
        extra={"path": request.url.path, "status_code": exc.status_code, "error_code": code},
    )
    return build_error_response(exc.status_code, code, str(exc.detail))


def register_error_handlers(app: FastAPI) -> None:
    """Register the handlers.

    Unexpected exceptions are handled by ``RequestContextMiddleware`` so the
    request ID is still available when the failure is logged.
    """
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_request_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
