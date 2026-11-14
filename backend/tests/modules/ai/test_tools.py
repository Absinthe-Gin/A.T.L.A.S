"""Tool registry and tool execution: the model's requests are never trusted."""

import uuid

import pytest

from app.modules.ai.exceptions import ToolRegistrationError
from app.modules.ai.execution_log import REDACTED, redact
from app.modules.ai.providers.base import ToolCall
from app.modules.ai.tools.executor import ToolExecutor
from app.modules.ai.tools.registry import ToolRegistry, to_definition
from app.shared.tools import ToolContext, ToolStatus
from tests.ai_support import (
    BadOutputTool,
    BusinessFailureTool,
    CrashingTool,
    EchoTool,
    SlowTool,
    build_registry,
    tool_call,
)

CONTEXT = ToolContext(user_id=uuid.uuid4(), conversation_id=uuid.uuid4(), request_id="req-1")
ALL_TOOLS = {"demo_echo", "demo_reject", "demo_crash", "demo_slow", "demo_bad_output"}


def _executor(timeout_seconds: float = 0.2) -> tuple[ToolExecutor, EchoTool]:
    echo = EchoTool()
    registry = build_registry(
        [echo, BusinessFailureTool(), CrashingTool(), SlowTool(), BadOutputTool()]
    )
    return ToolExecutor(registry, timeout_seconds), echo


# --- Registry ---------------------------------------------------------------


def test_registry_returns_registered_tools_by_name_and_domain() -> None:
    echo, other = EchoTool(), EchoTool(name="travel_echo", domain="travel")
    registry = build_registry([echo, other])

    assert registry.get("demo_echo") is echo
    assert registry.get("missing") is None
    assert registry.for_domain("travel") == [other]
    assert registry.for_domain("finance") == []
    assert registry.domains() == ["demo", "travel"]


def test_empty_registry_has_no_domains() -> None:
    assert ToolRegistry().domains() == []


def test_registry_rejects_a_duplicate_name() -> None:
    registry = build_registry([EchoTool()])

    with pytest.raises(ToolRegistrationError, match="already registered"):
        registry.register(EchoTool())


@pytest.mark.parametrize("name", ["Demo_Echo", "demo-echo", "de", "1demo_echo", "demo echo"])
def test_registry_rejects_an_invalid_name(name: str) -> None:
    with pytest.raises(ToolRegistrationError, match="Invalid tool name"):
        ToolRegistry().register(EchoTool(name=name))


def test_registry_rejects_a_name_outside_its_domain() -> None:
    with pytest.raises(ToolRegistrationError, match="<domain>_<action>"):
        ToolRegistry().register(EchoTool(name="finance_echo", domain="demo"))


def test_tool_definition_is_derived_from_the_input_model() -> None:
    definition = to_definition(EchoTool())

    assert definition.name == "demo_echo"
    assert definition.description == "Repeat the given text."
    assert definition.parameters["required"] == ["text"]
    assert set(definition.parameters["properties"]) == {"text", "repeat"}
    assert definition.parameters["properties"]["text"]["maxLength"] == 50


# --- Executor ---------------------------------------------------------------


async def test_valid_call_runs_the_tool_with_validated_input_and_trusted_context() -> None:
    executor, echo = _executor()

    result = await executor.execute(
        tool_call("demo_echo", text="chào", repeat=2), CONTEXT, ALL_TOOLS
    )

    assert result.status is ToolStatus.SUCCESS
    assert result.output == {"echoed": "chào chào", "user_id": str(CONTEXT.user_id)}
    assert result.error_code is None
    assert result.duration_ms >= 0
    received_context, received_input = echo.received[0]
    assert received_context is CONTEXT
    assert received_input.repeat == 2


async def test_default_values_of_the_input_model_are_applied() -> None:
    executor, echo = _executor()

    await executor.execute(tool_call("demo_echo", text="một"), CONTEXT, ALL_TOOLS)

    assert echo.received[0][1].repeat == 1


async def test_unknown_tool_is_reported_without_raising() -> None:
    executor, _ = _executor()

    result = await executor.execute(tool_call("finance_delete_everything"), CONTEXT, ALL_TOOLS)

    assert result.status is ToolStatus.ERROR
    assert result.error_code == "tool_not_found"
    assert result.output is None


async def test_tool_outside_the_allowed_set_is_not_executed() -> None:
    executor, echo = _executor()

    result = await executor.execute(tool_call("demo_echo", text="x"), CONTEXT, {"demo_slow"})

    assert result.error_code == "tool_not_found"
    assert echo.received == []


@pytest.mark.parametrize(
    ("arguments", "field"),
    [
        ({}, "text"),
        ({"text": ""}, "text"),
        ({"text": "x" * 51}, "text"),
        ({"text": "ok", "repeat": 0}, "repeat"),
        ({"text": "ok", "repeat": 99}, "repeat"),
        ({"text": "ok", "repeat": "nhiều"}, "repeat"),
        ({"text": None}, "text"),
    ],
)
async def test_invalid_arguments_are_rejected_before_execution(
    arguments: dict[str, object], field: str
) -> None:
    executor, echo = _executor()

    call = ToolCall(id="call-1", name="demo_echo", arguments=arguments)
    result = await executor.execute(call, CONTEXT, ALL_TOOLS)

    assert result.error_code == "invalid_tool_input"
    assert result.error_message is not None
    assert field in result.error_message
    assert echo.received == []


async def test_business_error_is_passed_on_with_its_code_and_message() -> None:
    executor, _ = _executor()

    result = await executor.execute(tool_call("demo_reject", text="x"), CONTEXT, ALL_TOOLS)

    assert result.status is ToolStatus.ERROR
    assert result.error_code == "budget_exceeded"
    assert result.error_message == "Vượt quá ngân sách."


async def test_unexpected_error_is_hidden_from_the_result_and_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    executor, _ = _executor()

    result = await executor.execute(tool_call("demo_crash", text="x"), CONTEXT, ALL_TOOLS)

    assert result.error_code == "tool_execution_failed"
    assert "secret internal detail" not in (result.error_message or "")
    crash_logs = [r for r in caplog.records if r.message == "Tool raised an unexpected error"]
    assert len(crash_logs) == 1
    assert crash_logs[0].exc_info is not None


async def test_slow_tool_is_stopped_by_the_timeout() -> None:
    executor, _ = _executor(timeout_seconds=0.05)

    result = await executor.execute(tool_call("demo_slow", text="x"), CONTEXT, ALL_TOOLS)

    assert result.error_code == "tool_timeout"
    assert result.duration_ms < 2000


async def test_output_that_breaks_the_contract_is_rejected() -> None:
    executor, _ = _executor()

    result = await executor.execute(tool_call("demo_bad_output", text="x"), CONTEXT, ALL_TOOLS)

    assert result.error_code == "invalid_tool_output"
    assert result.output is None


async def test_every_execution_is_logged_with_redacted_input(
    caplog: pytest.LogCaptureFixture,
) -> None:
    executor, _ = _executor()

    await executor.execute(
        tool_call("demo_echo", text="x", api_key="sk-secret-value"), CONTEXT, ALL_TOOLS
    )

    records = [r for r in caplog.records if r.message == "Tool executed"]
    assert len(records) == 1
    logged = records[0].__dict__
    assert logged["tool_name"] == "demo_echo"
    assert logged["status"] == "success"
    assert logged["conversation_id"] == str(CONTEXT.conversation_id)
    assert logged["tool_input"] == {"text": "x", "api_key": REDACTED}
    assert "sk-secret-value" not in str(logged)


# --- Redaction --------------------------------------------------------------


def test_redact_masks_sensitive_keys_at_any_depth() -> None:
    data = {
        "note": "ăn trưa",
        "Password": "p",
        "nested": {"access_token": "t", "items": [{"API_KEY": "k", "amount": 5}]},
    }

    assert redact(data) == {
        "note": "ăn trưa",
        "Password": REDACTED,
        "nested": {"access_token": REDACTED, "items": [{"API_KEY": REDACTED, "amount": 5}]},
    }


def test_redact_does_not_modify_its_argument() -> None:
    data = {"token": "t"}

    redact(data)

    assert data == {"token": "t"}
