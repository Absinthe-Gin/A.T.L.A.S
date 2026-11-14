import re
from typing import Any

from app.modules.ai.exceptions import ToolRegistrationError
from app.modules.ai.providers.base import ToolDefinition
from app.shared.tools import Tool

_VALID_NAME = re.compile(r"^[a-z][a-z0-9_]{2,63}$")

AnyTool = Tool[Any, Any]


class ToolRegistry:
    """The set of tools the assistant may request, filled at startup."""

    def __init__(self) -> None:
        self._tools: dict[str, AnyTool] = {}

    def register(self, tool: AnyTool) -> None:
        name = tool.spec.name
        if not _VALID_NAME.fullmatch(name):
            raise ToolRegistrationError(
                f"Invalid tool name {name!r}: use lowercase letters, digits and underscores."
            )
        if not name.startswith(f"{tool.spec.domain}_"):
            raise ToolRegistrationError(
                f"Tool {name!r} must be named '<domain>_<action>' with domain {tool.spec.domain!r}."
            )
        if name in self._tools:
            raise ToolRegistrationError(f"Tool {name!r} is already registered.")
        self._tools[name] = tool

    def get(self, name: str) -> AnyTool | None:
        return self._tools.get(name)

    def domains(self) -> list[str]:
        return sorted({tool.spec.domain for tool in self._tools.values()})

    def for_domain(self, domain: str) -> list[AnyTool]:
        return [tool for tool in self._tools.values() if tool.spec.domain == domain]


def to_definition(tool: AnyTool) -> ToolDefinition:
    """Describe a tool to the model. The schema is derived, never hand-written."""
    return ToolDefinition(
        name=tool.spec.name,
        description=tool.spec.description,
        parameters=tool.spec.input_model.model_json_schema(),
    )
