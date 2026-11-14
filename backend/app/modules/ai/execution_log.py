"""Structured log of what the assistant did, with sensitive values removed."""

import logging
import uuid
from typing import Any

from app.shared.tools import ToolResult

logger = logging.getLogger("app.modules.ai.execution")

REDACTED = "***"
_SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
)


def redact(value: Any) -> Any:
    """Return a copy of `value` with the values of sensitive-looking keys masked."""
    if isinstance(value, dict):
        return {
            key: REDACTED
            if any(part in str(key).lower() for part in _SENSITIVE_KEY_PARTS)
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def log_tool_execution(
    *, conversation_id: uuid.UUID, arguments: dict[str, Any], result: ToolResult
) -> None:
    logger.log(
        logging.INFO if result.succeeded else logging.WARNING,
        "Tool executed",
        extra={
            "conversation_id": str(conversation_id),
            "tool_name": result.tool_name,
            "tool_input": redact(arguments),
            "status": result.status.value,
            "error_code": result.error_code,
            "duration_ms": result.duration_ms,
        },
    )


def log_turn(
    *,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    intent: str,
    provider: str,
    model: str,
    iterations: int,
    tool_names: list[str],
    duration_ms: float,
    status: str,
) -> None:
    logger.info(
        "Chat turn completed",
        extra={
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "intent": intent,
            "provider": provider,
            "model": model,
            "iterations": iterations,
            "tools": tool_names,
            "duration_ms": duration_ms,
            "status": status,
        },
    )
