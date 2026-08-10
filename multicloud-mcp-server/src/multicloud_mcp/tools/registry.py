"""Registry for native MCP tools."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from multicloud_mcp.providers.base import ToolInfo


class NativeToolError(Exception):
    """Base error for native tool registry operations."""


class DuplicateToolError(NativeToolError):
    """Raised when a native MCP name is registered more than once."""


class NativeToolNotFoundError(NativeToolError):
    """Raised when a native MCP tool is not registered."""


class NativeTool(Protocol):
    """Common contract implemented by registered native tools."""

    @property
    def name(self) -> str:
        """Return the public MCP tool name."""
        ...

    def get_tool_info(self) -> ToolInfo:
        """Return MCP metadata."""
        ...

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute the native tool."""
        ...


Executor = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class RegisteredNativeTool:
    """Small adapter that gives existing native tools a shared contract."""

    info: ToolInfo
    executor: Executor

    @property
    def name(self) -> str:
        return self.info.name

    def get_tool_info(self) -> ToolInfo:
        return self.info

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self.executor(arguments)


class NativeToolRegistry:
    """Register, list, and execute enabled native MCP tools."""

    def __init__(self) -> None:
        self._tools: dict[str, NativeTool] = {}

    def register(self, tool: NativeTool) -> None:
        """Register a tool and reject duplicate public names."""
        if tool.name in self._tools:
            raise DuplicateToolError(f"Native tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> NativeTool:
        """Return a registered tool or raise a controlled lookup error."""
        try:
            return self._tools[name]
        except KeyError as exc:
            raise NativeToolNotFoundError(f"Native tool not found: {name}") from exc

    def get_optional(self, name: str) -> NativeTool | None:
        """Return a tool when registered, otherwise None."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolInfo]:
        """Return metadata for all registered tools."""
        return [tool.get_tool_info() for tool in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools
