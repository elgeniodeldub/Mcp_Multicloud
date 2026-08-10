"""Main MCP server entry point with stdio and HTTP transport support."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from multicloud_mcp.config import Settings
from multicloud_mcp.health import HealthMonitor
from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider
from multicloud_mcp.router import ProviderRouter, ToolNotFoundError

logger = structlog.get_logger()


class MulticloudMCPServer:
    """Unified Multicloud MCP Server."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.router = ProviderRouter()
        self.health_monitor = HealthMonitor(
            check_interval=30.0,
        )
        self.server = Server(settings.server.name)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools from all providers."""
            tools = await self.router.refresh_tools()

            if self.settings.multicloud.enabled:
                tools.extend(self._get_multicloud_tools())

            return [
                Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.input_schema,
                )
                for tool in tools
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Route tool call to appropriate provider."""
            try:
                if name.startswith("multicloud__"):
                    result = await self._call_multicloud_tool(name, arguments)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                result = await self.router.call_tool(name, arguments)
                self.health_monitor.record_result(
                    self.router.get_provider_for_tool(name).name,
                    not result.get("isError", False),
                )

                if result.get("isError"):
                    return [TextContent(type="text", text=f"Error: {result['content']}")]

                content_parts = []
                for item in result.get("content", []):
                    if item.get("type") == "text":
                        content_parts.append(item["text"])
                    else:
                        content_parts.append(json.dumps(item))

                return [TextContent(type="text", text="\n".join(content_parts))]

            except ToolNotFoundError as e:
                return [TextContent(type="text", text=f"Tool not found: {e}")]
            except Exception as e:
                logger.error("tool_call_failed", tool=name, error=str(e))
                return [TextContent(type="text", text=f"Internal error: {str(e)}")]

    def _get_multicloud_tools(self):
        """Return multicloud native tool definitions."""
        from multicloud_mcp.tools.cost_comparison import CostComparisonTool
        from multicloud_mcp.tools.resource_mapper import ResourceMapperTool

        tools = []
        if "cost_comparison" in self.settings.multicloud.tools:
            tools.append(CostComparisonTool().get_tool_info())
        if "resource_mapper" in self.settings.multicloud.tools:
            tools.append(ResourceMapperTool().get_tool_info())
        return tools

    async def _call_multicloud_tool(self, name: str, arguments: dict):
        """Execute multicloud native tools."""
        from multicloud_mcp.tools.cost_comparison import CostComparisonTool
        from multicloud_mcp.tools.resource_mapper import ResourceMapperTool

        if name == "multicloud__compare_cost":
            return await CostComparisonTool().execute(arguments)
        elif name == "multicloud__map_resource":
            return await ResourceMapperTool().execute(arguments)
        else:
            return {"error": f"Unknown multicloud tool: {name}"}

    async def initialize(self) -> None:
        """Initialize all configured providers."""
        for name, config in self.settings.providers.items():
            if not config.enabled:
                logger.info("provider_skipped", name=name, reason="disabled")
                continue

            try:
                if name == "aws":
                    provider = AWSProvider(
                        command=config.command,
                        args=config.args,
                        env=config.env,
                        timeout=config.timeout,
                    )
                elif name == "azure":
                    provider = AzureProvider(
                        command=config.command,
                        args=config.args,
                        env=config.env,
                        timeout=config.timeout,
                    )
                else:
                    logger.warning("unknown_provider", name=name)
                    continue

                await provider.connect()
                self.router.register_provider(provider)
                self.health_monitor.register_provider(name, provider)
                logger.info("provider_initialized", name=name)

            except Exception as e:
                logger.error("provider_init_failed", name=name, error=str(e))

        await self.router.refresh_tools(force=True)
        await self.health_monitor.start()

    async def shutdown(self) -> None:
        """Gracefully shutdown all providers."""
        await self.health_monitor.stop()
        for name, provider in self.router.providers.items():
            try:
                await provider.disconnect()
                logger.info("provider_shutdown", name=name)
            except Exception as e:
                logger.warning("provider_shutdown_error", name=name, error=str(e))

    async def run_stdio(self) -> None:
        """Run server with stdio transport."""
        await self.initialize()
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )
        finally:
            await self.shutdown()

    async def run_http(self) -> None:
        """Run server with HTTP transport (MCP 2026-07-28 stateless)."""
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        import uvicorn

        await self.initialize()

        async def mcp_endpoint(request: Request) -> JSONResponse:
            """Handle MCP requests over HTTP."""
            body = await request.json()
            method = body.get("method")
            params = body.get("params", {})

            if method == "tools/list":
                tools = await self.router.refresh_tools()
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": t.name,
                                "description": t.description,
                                "inputSchema": t.input_schema,
                            }
                            for t in tools
                        ]
                    }
                })

            elif method == "tools/call":
                result = await self.router.call_tool(
                    params.get("name"),
                    params.get("arguments", {})
                )
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": result
                })

            return JSONResponse({"error": "Method not found"}, status_code=404)

        app = Starlette(routes=[Route("/mcp", mcp_endpoint, methods=["POST"])])
        config = self.settings.server.http
        logger.info("http_server_starting", host=config.host, port=config.port)
        uvicorn.run(app, host=config.host, port=config.port)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Multicloud MCP Server")
    parser.add_argument(
        "--transport", choices=["stdio", "http"], default=None, help="Transport protocol"
    )
    parser.add_argument(
        "--port", type=int, default=None, help="HTTP port (only with --transport http)"
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to config YAML file"
    )
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None
    )
    args = parser.parse_args()

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    if args.config:
        settings = Settings.from_yaml(args.config)
    else:
        settings = Settings.load()

    if args.transport:
        settings.server.transport = args.transport
    if args.port:
        settings.server.http.port = args.port
    if args.log_level:
        settings.logging.level = args.log_level

    server = MulticloudMCPServer(settings)

    try:
        if settings.server.transport == "stdio":
            asyncio.run(server.run_stdio())
        else:
            asyncio.run(server.run_http())
    except KeyboardInterrupt:
        logger.info("server_shutdown_requested")
    except Exception as e:
        logger.error("server_fatal_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
