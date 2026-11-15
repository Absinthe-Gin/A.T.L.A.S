import asyncio
import logging
import time
from collections.abc import Collection
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.exceptions import AppError
from app.modules.ai.execution_log import log_tool_execution
from app.modules.ai.providers.base import ToolCall
from app.modules.ai.tools.registry import ToolRegistry
from app.shared.tools import Tool, ToolContext, ToolEffect, ToolResult, ToolStatus

logger = logging.getLogger(__name__)

AnyTool = Tool[Any, Any]


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

        if tool.spec.effect is ToolEffect.WRITE:
            # The model may only propose a change; the user decides.
            return await self._propose(tool, tool_input, context)
        return await self._invoke(tool, tool_input, context)

    async def execute_confirmed(
        self, tool_name: str, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        """Run a write request the user has confirmed. Arguments are validated again."""
        started_at = time.perf_counter()
        tool = self._registry.get(tool_name)
        if tool is None:
            result = ToolResult(
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                error_code="tool_not_found",
                error_message=f"Tool '{tool_name}' is not available.",
            )
        else:
            try:
                tool_input = tool.spec.input_model.model_validate(arguments)
            except ValidationError as error:
                result = ToolResult(
                    tool_name=tool_name,
                    status=ToolStatus.ERROR,
                    error_code="invalid_tool_input",
                    error_message=_describe(error),
                )
            else:
                result = await self._invoke(tool, tool_input, context)
        result.duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log_tool_execution(
            conversation_id=context.conversation_id, arguments=arguments, result=result
        )
        return result

    async def _propose(
        self, tool: AnyTool, tool_input: BaseModel, context: ToolContext
    ) -> ToolResult:
        name = tool.spec.name
        try:
            async with asyncio.timeout(self._timeout_seconds):
                summary = await tool.preview(context, tool_input)
        except TimeoutError:
            return _failure(
                name, "tool_timeout", f"Tool did not finish within {self._timeout_seconds} seconds."
            )
        except AppError as error:
            return _failure(name, error.code, error.message)
        except Exception:
            logger.exception("Tool preview raised an unexpected error", extra={"tool_name": name})
            return _failure(name, "tool_execution_failed", "The tool failed unexpectedly.")
        return ToolResult(
            tool_name=name,
            status=ToolStatus.PENDING,
            output={"summary": summary, "arguments": tool_input.model_dump(mode="json")},
        )

    async def _invoke(
        self, tool: AnyTool, tool_input: BaseModel, context: ToolContext
    ) -> ToolResult:
        name = tool.spec.name

        def failure(code: str, message: str) -> ToolResult:
            return _failure(name, code, message)

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
            logger.exception("Tool raised an unexpected error", extra={"tool_name": name})
            return failure("tool_execution_failed", "The tool failed unexpectedly.")

        try:
            output = tool.spec.output_model.model_validate(raw_output, from_attributes=True)
        except ValidationError:
            # The tool broke its own contract: a programming error.
            logger.exception("Tool returned an invalid output", extra={"tool_name": name})
            return failure("invalid_tool_output", "The tool returned an invalid result.")

        return ToolResult(
            tool_name=name, status=ToolStatus.SUCCESS, output=output.model_dump(mode="json")
        )


def _failure(tool_name: str, code: str, message: str) -> ToolResult:
    return ToolResult(
        tool_name=tool_name, status=ToolStatus.ERROR, error_code=code, error_message=message
    )
