"""Main MCP server entry point with stdio and HTTP transport support."""

from __future__ import annotations

import argparse
import asyncio
import json
import signal
import sys
import time
import uuid
from typing import Any

import structlog
import uvicorn
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

from multicloud_mcp.config import Settings
from multicloud_mcp.health import HealthMonitor
from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider
from multicloud_mcp.providers.base import ProviderAdapter, ToolInfo
from multicloud_mcp.router import ProviderRouter, ToolNotFoundError
from multicloud_mcp.security import ToolBlockedError, ToolSecurityPolicy
from multicloud_mcp.security.auth import BearerAuthenticator
from multicloud_mcp.security.middleware import SecurityMiddleware
from multicloud_mcp.security.rate_limit import InMemoryRateLimiter

logger = structlog.get_logger()


class MulticloudMCPServer:
    """Unified Multicloud MCP Server."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.router = ProviderRouter()
        self.health_monitor = HealthMonitor(check_interval=30.0)
        self.server = Server(settings.server.name)
        self.security_policy = ToolSecurityPolicy(settings.security.tool_policy.mode)
        self.http_metrics: dict[str, int] = {
            "requests": 0,
            "auth_failures": 0,
            "rate_limit_rejections": 0,
            "request_size_rejections": 0,
            "tool_calls": 0,
            "tool_policy_rejections": 0,
        }
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
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

        @self.server.call_tool()  # type: ignore[untyped-decorator]
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Route tool call to appropriate provider."""
            try:
                self.security_policy.authorize_tool(name)
                if name.startswith(("multicloud__", "finops__")):
                    result = await self._call_multicloud_tool(name, arguments)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                result = await self.router.call_tool(name, arguments)
                provider = self.router.get_provider_for_tool(name)
                if provider:
                    self.health_monitor.record_result(
                        provider.name,
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
            except ToolBlockedError as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "tool_blocked_by_policy",
                                "tool": e.tool_name,
                                "policy": e.policy,
                            }
                        ),
                    )
                ]
            except Exception as e:
                logger.error("tool_call_failed", tool=name, transport="stdio", error=str(e))
                return [TextContent(type="text", text="Internal server error")]

    def _get_multicloud_tools(self) -> list[ToolInfo]:
        """Return multicloud native tool definitions."""
        from multicloud_mcp.tools.actual_costs import ActualCostsTool
        from multicloud_mcp.tools.compliance import ComplianceCheckerTool
        from multicloud_mcp.tools.discover_resources import DiscoverResourcesTool
        from multicloud_mcp.tools.list_price_comparison import ListPriceComparisonTool
        from multicloud_mcp.tools.list_providers import ListProvidersTool
        from multicloud_mcp.tools.resource_mapper import ResourceMapperTool
        from multicloud_mcp.tools.security_posture import SecurityPostureTool

        tools = []
        enabled = set(self.settings.multicloud.tools)

        if "actual_costs" in enabled:
            tools.append(ActualCostsTool().get_tool_info())
        if "list_price_comparison" in enabled:
            tools.append(ListPriceComparisonTool().get_tool_info())
        if "resource_mapper" in enabled:
            tools.append(ResourceMapperTool().get_tool_info())
        if "list_providers" in enabled:
            tools.append(ListProvidersTool().get_tool_info())
        if "discover_resources" in enabled:
            tools.append(DiscoverResourcesTool().get_tool_info())
        if "security_posture" in enabled:
            tools.append(SecurityPostureTool().get_tool_info())
        if "compliance_checker" in enabled:
            tools.append(ComplianceCheckerTool().get_tool_info())

        return tools

    async def _call_multicloud_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute multicloud native tools."""
        from multicloud_mcp.tools.actual_costs import ActualCostsTool
        from multicloud_mcp.tools.compliance import ComplianceCheckerTool
        from multicloud_mcp.tools.discover_resources import DiscoverResourcesTool
        from multicloud_mcp.tools.list_price_comparison import ListPriceComparisonTool
        from multicloud_mcp.tools.list_providers import ListProvidersTool
        from multicloud_mcp.tools.resource_mapper import ResourceMapperTool
        from multicloud_mcp.tools.security_posture import SecurityPostureTool

        if name == "finops__get_actual_costs":
            return await ActualCostsTool().execute(arguments)
        elif name == "finops__compare_list_prices":
            return await ListPriceComparisonTool().execute(arguments)
        elif name == "multicloud__map_resource":
            return await ResourceMapperTool().execute(arguments)
        elif name == "multicloud__list_providers":
            return await ListProvidersTool().execute(arguments, self.router, self.health_monitor)
        elif name == "multicloud__discover_resources":
            return await DiscoverResourcesTool().execute(arguments, self.router)
        elif name == "multicloud__security_posture":
            return await SecurityPostureTool().execute(arguments, self.router)
        elif name == "multicloud__compliance_check":
            return await ComplianceCheckerTool().execute(arguments, self.router)
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
                    provider: ProviderAdapter = AWSProvider(
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

    def create_http_app(self) -> Starlette:
        """Create the secured HTTP application without starting a listener."""

        async def mcp_endpoint(request: Request) -> JSONResponse:
            """Handle MCP requests over HTTP."""
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            try:
                body = await request.json()
            except Exception:
                return self._jsonrpc_error(None, -32600, "invalid_request", 400, request_id)

            try:
                method = body.get("method")
                params = body.get("params", {})

                if method == "tools/list":
                    tools = await self.router.refresh_tools()
                    if self.settings.multicloud.enabled:
                        tools.extend(self._get_multicloud_tools())
                    return JSONResponse(
                        {
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
                            },
                        }
                    )

                if method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    if not isinstance(tool_name, str):
                        return self._jsonrpc_error(
                            body.get("id"), -32602, "invalid_request", 400, request_id
                        )

                    started = time.perf_counter()
                    success = False
                    provider = tool_name.split("__", 1)[0]
                    try:
                        self.security_policy.authorize_tool(tool_name)
                        if tool_name.startswith(("multicloud__", "finops__")):
                            result = await self._call_multicloud_tool(tool_name, arguments)
                            result = {
                                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                            }
                        else:
                            result = await self.router.call_tool(tool_name, arguments)
                        success = not result.get("isError", False)
                        return JSONResponse(
                            {"jsonrpc": "2.0", "id": body.get("id"), "result": result}
                        )
                    except ToolBlockedError as error:
                        self.http_metrics["tool_policy_rejections"] += 1
                        return self._jsonrpc_error(
                            body.get("id"),
                            -32003,
                            "tool_blocked_by_policy",
                            403,
                            request_id,
                            {"tool": error.tool_name, "policy": error.policy},
                        )
                    except ToolNotFoundError:
                        return self._jsonrpc_error(
                            body.get("id"), -32601, "tool_not_found", 404, request_id
                        )
                    finally:
                        self.http_metrics["tool_calls"] += 1
                        logger.info(
                            "mcp_tool_call",
                            event="mcp_tool_call",
                            request_id=request_id,
                            tool=tool_name,
                            provider=provider,
                            transport="http",
                            client_ip=getattr(request.state, "client_ip", "unknown"),
                            success=success,
                            duration_ms=round((time.perf_counter() - started) * 1000, 2),
                            policy=self.security_policy.mode,
                        )

                return self._jsonrpc_error(
                    body.get("id"), -32601, "invalid_request", 404, request_id
                )
            except Exception as error:
                logger.error(
                    "http_request_failed",
                    request_id=request_id,
                    error=str(error),
                    transport="http",
                    event="http_request_failed",
                )
                return self._jsonrpc_error(
                    body.get("id") if isinstance(body, dict) else None,
                    -32603,
                    "Internal server error",
                    500,
                    request_id,
                )

        async def health_endpoint(request: Request) -> JSONResponse:
            """Health check endpoint."""
            health = await self.router.health_check_all()
            return JSONResponse(
                {
                    "status": "healthy" if all(h.healthy for h in health.values()) else "degraded",
                    "providers": {
                        name: {
                            "healthy": h.healthy,
                            "tools_count": h.tools_count,
                            "latency_ms": h.latency_ms,
                        }
                        for name, h in health.items()
                    },
                }
            )

        async def metrics_endpoint(request: Request) -> PlainTextResponse:
            """Prometheus-style metrics endpoint."""
            lines = [
                "# HELP multicloud_providers_total Number of registered providers",
                "# TYPE multicloud_providers_total gauge",
                f"multicloud_providers_total {len(self.router.providers)}",
                "",
                "# HELP multicloud_tools_total Number of available tools",
                "# TYPE multicloud_tools_total gauge",
                f"multicloud_tools_total {len(self.router.all_tools)}",
                "# TYPE multicloud_http_requests_total counter",
                f"multicloud_http_requests_total {self.http_metrics['requests']}",
                "# TYPE multicloud_http_auth_failures_total counter",
                f"multicloud_http_auth_failures_total {self.http_metrics['auth_failures']}",
                "# TYPE multicloud_http_rate_limit_rejections_total counter",
                f"multicloud_http_rate_limit_rejections_total {self.http_metrics['rate_limit_rejections']}",
                "# TYPE multicloud_tool_calls_total counter",
                f"multicloud_tool_calls_total {self.http_metrics['tool_calls']}",
                "# TYPE multicloud_tool_policy_rejections_total counter",
                f"multicloud_tool_policy_rejections_total {self.http_metrics['tool_policy_rejections']}",
            ]
            return PlainTextResponse("\n".join(lines))

        routes = [
            Route("/mcp", mcp_endpoint, methods=["POST"]),
            Route("/health", health_endpoint, methods=["GET"]),
            Route("/metrics", metrics_endpoint, methods=["GET"]),
        ]

        security = self.settings.security
        if security.authentication.enabled and "*" in security.cors.allowed_origins:
            raise ValueError(
                "security.cors.allowed_origins cannot contain '*' when authentication is enabled"
            )
        authenticator = BearerAuthenticator(
            security.authentication.enabled, security.authentication.api_key_env
        )
        limiter = (
            InMemoryRateLimiter(security.rate_limit.requests_per_minute)
            if security.rate_limit.enabled
            else None
        )
        app = Starlette(routes=routes)
        app.add_middleware(
            SecurityMiddleware,
            authenticator=authenticator,
            protect_metrics=security.authentication.protect_metrics,
            max_request_size=security.max_request_size_bytes,
            rate_limiter=limiter,
            metrics=self.http_metrics,
        )
        if security.cors.enabled:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=security.cors.allowed_origins,
                allow_methods=security.cors.allowed_methods,
                allow_headers=security.cors.allowed_headers,
            )
        return app

    @staticmethod
    def _jsonrpc_error(
        request_id: Any,
        code: int,
        message: str,
        status: int,
        correlation_id: str,
        data: dict[str, Any] | None = None,
    ) -> JSONResponse:
        error: dict[str, Any] = {"code": code, "message": message}
        if data:
            error["data"] = data
        return JSONResponse(
            {"jsonrpc": "2.0", "id": request_id, "error": error, "request_id": correlation_id},
            status_code=status,
        )

    async def run_http(self) -> None:
        """Run server with secured HTTP transport."""
        await self.initialize()
        app = self.create_http_app()

        config = self.settings.server.http
        logger.info("http_server_starting", host=config.host, port=config.port)

        # Graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

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
    parser.add_argument("--config", type=str, default=None, help="Path to config YAML file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None)
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

    settings = Settings.from_yaml(args.config) if args.config else Settings.load()

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
