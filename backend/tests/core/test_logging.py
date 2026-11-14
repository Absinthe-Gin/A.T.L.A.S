import json
import logging
import sys

from app.core.config import LogFormat
from app.core.logging import (
    ConsoleFormatter,
    JsonFormatter,
    RequestIdFilter,
    configure_logging,
)
from app.core.request_context import reset_request_id, set_request_id


def _record(message: str = "hello", **extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="app.modules.finance.service",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
        func="create_transaction",
    )
    record.__dict__.update(extra)
    return record


def test_json_formatter_outputs_the_standard_fields() -> None:
    record = _record("Giao dịch đã tạo", transaction_id="abc", amount=50000)
    record.request_id = "req-1"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "WARNING"
    assert payload["logger"] == "app.modules.finance.service"
    assert payload["function"] == "create_transaction"
    assert payload["message"] == "Giao dịch đã tạo"
    assert payload["request_id"] == "req-1"
    assert payload["transaction_id"] == "abc"
    assert payload["amount"] == 50000
    assert payload["timestamp"].endswith("+00:00")


def test_json_formatter_includes_the_stack_trace() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = _record("failed")
        record.exc_info = sys.exc_info()

    payload = json.loads(JsonFormatter().format(record))

    assert "ValueError: boom" in payload["exception"]


def test_json_formatter_serialises_unusual_values() -> None:
    record = _record(payload_object=object())

    payload = json.loads(JsonFormatter().format(record))

    assert isinstance(payload["payload_object"], str)


def test_console_formatter_shows_request_id_and_extra_fields() -> None:
    record = _record("Request completed", status_code=200)
    record.request_id = "req-2"

    line = ConsoleFormatter().format(record)

    assert "[req-2]" in line
    assert "app.modules.finance.service.create_transaction: Request completed" in line
    assert "status_code=200" in line


def test_console_formatter_works_without_a_request_id() -> None:
    line = ConsoleFormatter().format(_record())

    assert "[None]" in line


def test_request_id_filter_reads_the_current_request_context() -> None:
    record = _record()
    token = set_request_id("req-3")
    try:
        RequestIdFilter().filter(record)
    finally:
        reset_request_id(token)

    assert record.request_id == "req-3"  # type: ignore[attr-defined]


def test_configure_logging_does_not_duplicate_the_handler() -> None:
    configure_logging("INFO", LogFormat.JSON)
    configure_logging("DEBUG", LogFormat.CONSOLE)

    root = logging.getLogger()
    app_handlers = [handler for handler in root.handlers if handler.get_name() == "app"]

    assert len(app_handlers) == 1
    assert isinstance(app_handlers[0].formatter, ConsoleFormatter)
    assert root.level == logging.DEBUG
