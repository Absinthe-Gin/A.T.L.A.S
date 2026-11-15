"""Structured logging configuration.

Every record carries the current request ID. Context passed through
``logger.info("...", extra={...})`` is preserved by both formatters.
"""

import json
import logging
import sys
from datetime import UTC, datetime

from app.core.config import LogFormat
from app.core.request_context import get_request_id

_HANDLER_NAME = "app"
_NOISY_LOGGERS = ("aiosqlite", "asyncio", "httpcore", "httpx")

# Attributes that exist on every LogRecord; anything else came from `extra`.
_STANDARD_ATTRIBUTES = frozenset(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
    "request_id",
    # Added by uvicorn: a duplicate of the message with terminal colour codes.
    "color_message",
}


def _extra_fields(record: logging.LogRecord) -> dict[str, object]:
    return {key: value for key, value in record.__dict__.items() if key not in _STANDARD_ATTRIBUTES}


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    """Render one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        payload.update(_extra_fields(record))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """Render a human-readable line for local development."""

    def __init__(self) -> None:
        super().__init__(
            fmt=("%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s.%(funcName)s: %(message)s")
        )

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = None
        line = super().format(record)
        extras = _extra_fields(record)
        if not extras:
            return line
        # Stack traces must stay last, so insert extras before the first newline.
        head, separator, tail = line.partition("\n")
        rendered = " ".join(f"{key}={value!r}" for key, value in extras.items())
        return f"{head} | {rendered}{separator}{tail}"


def configure_logging(level: str, log_format: LogFormat) -> None:
    """Install the application log handler on the root logger.

    Safe to call more than once: only the handler installed by a previous
    call is replaced, handlers owned by other tools are left untouched.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.set_name(_HANDLER_NAME)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter() if log_format is LogFormat.JSON else ConsoleFormatter())

    root = logging.getLogger()
    for existing in [h for h in root.handlers if h.get_name() == _HANDLER_NAME]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    # These libraries log every low-level operation, which hides application
    # messages. httpx also logs each request URL at INFO, and a URL may carry an
    # API key (SerpApi), so only warnings from them are kept.
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    # Route uvicorn's own messages through the application handler.
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True

    # The request middleware writes the access log, with the request ID.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
