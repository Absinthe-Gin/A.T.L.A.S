import asyncio
import logging
import time
from collections.abc import Collection

from pydantic import ValidationError

from app.core.exceptions import AppError
from app.modules.ai.execution_log import log_tool_execution
from app.modules.ai.providers.base import ToolCall
from app.modules.ai.tools.registry import ToolRegistry
from app.shared.tools import ToolContext, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


def _describe(error: ValidationError) -> str:
    """Summarise validation errors so the model can correct its arguments."""
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc']) or 'input'}: {item['msg']}"
        for item in error.errors()
    )


class ToolExecutor:
    """Run a tool requested by the model, treating the request as untrusted.

    Every failure becomes a `ToolResult` so the conversation can continue.
    """

    def __init__(self, registry: ToolRegistry, timeout_seconds: float) -> None:
        self._registry = registry
        self._timeout_seconds = timeout_seconds

    async def execute(
        self, call: ToolCall, context: ToolContext, allowed_tools: Collection[str]
    ) -> ToolResult:
        started_at = time.perf_counter()
        result = await self._run(call, context, allowed_tools)
        result.duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log_tool_execution(
            conversation_id=context.conversation_id, arguments=call.arguments, result=result
        )
        return result

    async def _run(
        self, call: ToolCall, context: ToolContext, allowed_tools: Collection[str]
    ) -> ToolResult:
        def failure(code: str, message: str) -> ToolResult:
            return ToolResult(
                tool_name=call.name, status=ToolStatus.ERROR, error_code=code, error_message=message
            )

        tool = self._registry.get(call.name)
        # A tool outside the current intent is treated exactly like a missing one.
        if tool is None or call.name not in allowed_tools:
            return failure("tool_not_found", f"Tool '{call.name}' is not available.")

        try:
            tool_input = tool.spec.input_model.model_validate(call.arguments)
        except ValidationError as error:
            return failure("invalid_tool_input", _describe(error))

        try:
            async with asyncio.timeout(self._timeout_seconds):
                raw_output = await tool.execute(context, tool_input)
        except TimeoutError:
            return failure(
                "tool_timeout", f"Tool did not finish within {self._timeout_seconds} seconds."
            )
        except AppError as error:
            # An expected business or validation failure: safe to show to the model.
            return failure(error.code, error.message)
        except Exception:
            logger.exception("Tool raised an unexpected error", extra={"tool_name": call.name})
            return failure("tool_execution_failed", "The tool failed unexpectedly.")

        try:
            output = tool.spec.output_model.model_validate(raw_output, from_attributes=True)
        except ValidationError:
            # The tool broke its own contract: a programming error.
            logger.exception("Tool returned an invalid output", extra={"tool_name": call.name})
            return failure("invalid_tool_output", "The tool returned an invalid result.")

        return ToolResult(
            tool_name=call.name, status=ToolStatus.SUCCESS, output=output.model_dump(mode="json")
        )
