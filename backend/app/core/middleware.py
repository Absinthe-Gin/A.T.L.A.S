"""Request-scoped middleware: request ID, access log, last-resort error handling."""

import logging
import re
import time
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.error_handlers import build_internal_error_response
from app.core.request_context import reset_request_id, set_request_id

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

# A client-supplied ID is written to logs, so only a safe shape is accepted.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def _resolve_request_id(scope: Scope) -> str:
    supplied = Headers(scope=scope).get(REQUEST_ID_HEADER)
    if supplied and _VALID_REQUEST_ID.fullmatch(supplied):
        return supplied
    return uuid.uuid4().hex


class RequestContextMiddleware:
    """Give every HTTP request an ID, log it, and catch unexpected errors.

    Implemented as plain ASGI middleware so the request ID context variable
    is set in the same task that runs the endpoint.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _resolve_request_id(scope)
        token = set_request_id(request_id)
        started_at = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception(
                "Unhandled exception",
                extra={"method": scope["method"], "path": scope["path"]},
            )
            if response_started:
                # Headers are already sent; the response cannot be replaced.
                raise
            response = build_internal_error_response()
            await response(scope, receive, send_with_request_id)
        finally:
            logger.info(
                "Request completed",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                },
            )
            reset_request_id(token)
