"""AWS MCP Server adapter using stdio transport."""

from __future__ import annotations

import time
from typing import Any

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo

logger = structlog.get_logger()


class AWSProvider(ProviderAdapter):
    """Adapter for the official AWS MCP Server (awslabs/mcp)."""

    def __init__(
        self,
        command: str = "uvx",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 60,
    ) -> None:
        super().__init__(
            name="aws",
            namespace="aws",
            command=command,
            args=args or ["awslabs.core-mcp-server@latest"],
            env=env or {},
            timeout=timeout,
        )
        self._session: ClientSession | None = None
        self._stdio_ctx = None
        self._client_ctx = None

    async def connect(self) -> None:
        """Connect to AWS MCP Server via stdio."""
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

            self._logger.info("aws_provider.connected")
        except Exception as e:
            self._logger.error("aws_provider.connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from AWS MCP Server."""
        try:
            if self._client_ctx:
                await self._client_ctx.__aexit__(None, None, None)
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
            self._session = None
            self._logger.info("aws_provider.disconnected")
        except Exception as e:
            self._logger.warning("aws_provider.disconnect_error", error=str(e))

    async def list_tools(self) -> list[ToolInfo]:
        """List tools from AWS MCP Server with namespace prefix."""
        if not self._session:
            await self.connect()

        try:
            tools_response = await self._session.list_tools()
            self._tools = []

            for tool in tools_response.tools:
                namespaced = self._namespaced_name(tool.name)
                self._tools.append(
                    ToolInfo(
                        name=namespaced,
                        description=f"[AWS] {tool.description}",
                        input_schema=tool.inputSchema,
                        original_name=tool.name,
                        provider="aws",
                        namespace="aws",
                    )
                )

            self.health.tools_count = len(self._tools)
            self._logger.info("aws_provider.tools_loaded", count=len(self._tools))
            return self._tools

        except Exception as e:
            self._logger.error("aws_provider.list_tools_failed", error=str(e))
            self.health.healthy = False
            self.health.error_message = str(e)
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on AWS MCP Server."""
        if not self._session:
            await self.connect()

        original_name = self._original_name(tool_name)

        try:
            self._logger.debug(
                "aws_provider.calling_tool",
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
                "aws_provider.tool_call_failed",
                tool=original_name,
                error=str(e),
            )
            return {
                "content": [{"type": "text", "text": f"AWS Error: {str(e)}"}],
                "isError": True,
            }

    async def health_check(self) -> ProviderHealth:
        """Check AWS MCP Server health by listing tools."""
        start = time.time()
        try:
            if not self._session:
                await self.connect()

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
            self._logger.warning("aws_provider.health_check_failed", error=str(e))

        return self.health
