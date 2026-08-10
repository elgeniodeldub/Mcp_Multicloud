"""Azure MCP Server adapter using stdio transport."""

from __future__ import annotations

import time
from typing import Any

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo

logger = structlog.get_logger()


class AzureProvider(ProviderAdapter):
    """Adapter for the official Azure MCP Server (microsoft/mcp)."""

    def __init__(
        self,
        command: str = "npx",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 60,
    ) -> None:
        super().__init__(
            name="azure",
            namespace="azure",
            command=command,
            args=args or ["-y", "@azure/mcp@2.0.5"],
            env=env or {},
            timeout=timeout,
        )
        self._session: ClientSession | None = None
        self._stdio_ctx: Any = None
        self._client_ctx: Any = None

    async def connect(self) -> None:
        """Connect to Azure MCP Server via stdio."""
        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env,
            )
            self._stdio_ctx = stdio_client(server_params)
            read, write = await self._stdio_ctx.__aenter__()

            self._client_ctx = ClientSession(read, write)
            self._session = await self._client_ctx.__aenter__()
            await self._session.initialize()

            self._logger.info("azure_provider.connected")
        except Exception as e:
            self._logger.error("azure_provider.connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from Azure MCP Server."""
        try:
            if self._client_ctx:
                await self._client_ctx.__aexit__(None, None, None)
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
            self._session = None
            self._logger.info("azure_provider.disconnected")
        except Exception as e:
            self._logger.warning("azure_provider.disconnect_error", error=str(e))

    async def list_tools(self) -> list[ToolInfo]:
        """List tools from Azure MCP Server with namespace prefix."""
        if not self._session:
            await self.connect()
        assert self._session is not None

        try:
            tools_response = await self._session.list_tools()
            self._tools = []

            for tool in tools_response.tools:
                namespaced = self._namespaced_name(tool.name)
                self._tools.append(
                    ToolInfo(
                        name=namespaced,
                        description=f"[Azure] {tool.description}",
                        input_schema=tool.inputSchema,
                        original_name=tool.name,
                        provider="azure",
                        namespace="azure",
                    )
                )

            self.health.tools_count = len(self._tools)
            self._logger.info("azure_provider.tools_loaded", count=len(self._tools))
            return self._tools

        except Exception as e:
            self._logger.error("azure_provider.list_tools_failed", error=str(e))
            self.health.healthy = False
            self.health.error_message = str(e)
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on Azure MCP Server."""
        if not self._session:
            await self.connect()
        assert self._session is not None

        original_name = self._original_name(tool_name)

        try:
            self._logger.debug(
                "azure_provider.calling_tool",
                namespaced=tool_name,
                original=original_name,
            )

            result = await self._session.call_tool(original_name, arguments)

            content = []
            for item in result.content:
                if hasattr(item, "text"):
                    content.append({"type": "text", "text": item.text})
                elif hasattr(item, "data"):
                    content.append({"type": "resource", "data": item.data})
                else:
                    content.append({"type": "text", "text": str(item)})

            return {
                "content": content,
                "isError": result.isError if hasattr(result, "isError") else False,
            }

        except Exception as e:
            self._logger.error(
                "azure_provider.tool_call_failed",
                tool=original_name,
                error=str(e),
            )
            return {
                "content": [{"type": "text", "text": f"Azure Error: {str(e)}"}],
                "isError": True,
            }

    async def health_check(self) -> ProviderHealth:
        """Check Azure MCP Server health by listing tools."""
        start = time.time()
        try:
            if not self._session:
                await self.connect()
            assert self._session is not None

            await self._session.list_tools()

            self.health.healthy = True
            self.health.last_check = time.time()
            self.health.latency_ms = (time.time() - start) * 1000
            self.health.error_message = None

        except Exception as e:
            self.health.healthy = False
            self.health.last_check = time.time()
            self.health.latency_ms = (time.time() - start) * 1000
            self.health.error_message = str(e)
            self._logger.warning("azure_provider.health_check_failed", error=str(e))

        return self.health
