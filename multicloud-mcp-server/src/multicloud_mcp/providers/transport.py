"""Transport abstraction for upstream MCP provider sessions."""

from __future__ import annotations

from typing import Any, Protocol

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ProviderTransport(Protocol):
    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    async def list_tools(self) -> Any: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...


class StdioMCPTransport:
    """Current stdio MCP transport implementation."""

    def __init__(self, command: str, args: list[str], env: dict[str, str]) -> None:
        self.command = command
        self.args = args
        self.env = env
        self._stdio_context: Any = None
        self._client_context: Any = None
        self._session: ClientSession | None = None

    @property
    def session(self) -> ClientSession | None:
        return self._session

    async def connect(self) -> None:
        params = StdioServerParameters(command=self.command, args=self.args, env=self.env)
        self._stdio_context = stdio_client(params)
        read, write = await self._stdio_context.__aenter__()
        self._client_context = ClientSession(read, write)
        self._session = await self._client_context.__aenter__()
        await self._session.initialize()

    async def disconnect(self) -> None:
        if self._client_context:
            await self._client_context.__aexit__(None, None, None)
        if self._stdio_context:
            await self._stdio_context.__aexit__(None, None, None)
        self._session = None
        self._client_context = None
        self._stdio_context = None

    async def list_tools(self) -> Any:
        if self._session is None:
            raise ConnectionError("MCP transport is not connected")
        return await self._session.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if self._session is None:
            raise ConnectionError("MCP transport is not connected")
        return await self._session.call_tool(name, arguments)
