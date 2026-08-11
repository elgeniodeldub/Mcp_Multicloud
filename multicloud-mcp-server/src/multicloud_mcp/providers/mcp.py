"""Reusable adapter for providers backed by upstream MCP servers."""

from __future__ import annotations

import time
from typing import Any

from multicloud_mcp.domain.exceptions import CapabilityNotSupportedError
from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo, ToolSafety
from multicloud_mcp.providers.capabilities import Capability
from multicloud_mcp.providers.resilience import ProviderCircuitBreaker, ResilientExecutor
from multicloud_mcp.providers.transport import ProviderTransport, StdioMCPTransport


class MCPProviderAdapter(ProviderAdapter):
    """Generic MCP lifecycle, routing, timeout, retry, and capability behavior."""

    _capability_tools: dict[Capability, tuple[str, ...]] = {}

    def __init__(
        self,
        name: str,
        namespace: str,
        command: str,
        args: list[str],
        env: dict[str, str],
        timeout: int = 60,
        max_concurrency: int = 10,
        retry_attempts: int = 2,
        circuit_failure_threshold: int = 5,
        circuit_recovery_timeout: float = 30.0,
        transport: ProviderTransport | None = None,
    ) -> None:
        super().__init__(
            name,
            namespace,
            command,
            args,
            env,
            timeout,
            max_concurrency,
            retry_attempts,
            circuit_failure_threshold,
            circuit_recovery_timeout,
        )
        self.transport = transport or StdioMCPTransport(command, args, env)
        self.resilience = ResilientExecutor(
            name,
            timeout,
            retry_attempts,
            max_concurrency,
            ProviderCircuitBreaker(circuit_failure_threshold, circuit_recovery_timeout),
        )

    async def connect(self) -> None:
        await self.resilience.run(self.transport.connect)
        self._logger.info("provider_connected")

    async def disconnect(self) -> None:
        try:
            await self.transport.disconnect()
        finally:
            self._tools = []
            self._logger.info("provider_disconnected")

    async def list_tools(self) -> list[ToolInfo]:
        if not self._tools:
            if getattr(self.transport, "session", None) is None:
                await self.connect()
            response = await self.resilience.run(self.transport.list_tools)
            self._tools = [
                ToolInfo(
                    name=self._namespaced_name(tool.name),
                    description=f"[{self.name.upper()}] {tool.description}",
                    input_schema=tool.inputSchema,
                    original_name=tool.name,
                    provider=self.name,
                    namespace=self.namespace,
                    safety=(
                        ToolSafety.MUTATING
                        if any(
                            verb in tool.name.lower().split("__")
                            for verb in ("create", "delete", "remove", "terminate", "update", "modify", "start", "stop", "deploy", "execute")
                        )
                        else ToolSafety.READ_ONLY
                    ),
                )
                for tool in response.tools
            ]
            self.health.tools_count = len(self._tools)
        return self._tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._tools:
            await self.list_tools()
        original_name = self._original_name(tool_name)
        try:
            result = await self.resilience.run(
                lambda: self.transport.call_tool(original_name, arguments)
            )
            content = []
            for item in result.content:
                if hasattr(item, "text"):
                    content.append({"type": "text", "text": item.text})
                elif hasattr(item, "data"):
                    content.append({"type": "resource", "data": item.data})
                else:
                    content.append({"type": "text", "text": str(item)})
            return {"content": content, "isError": getattr(result, "isError", False)}
        except Exception as exc:
            self._logger.error(
                "provider_tool_call_failed", tool=original_name, error_type=type(exc).__name__
            )
            return {
                "content": [{"type": "text", "text": f"{self.name.upper()} provider error"}],
                "isError": True,
            }

    async def health_check(self) -> ProviderHealth:
        started = time.perf_counter()
        try:
            await self.list_tools()
            self.health.healthy = True
            self.health.error_message = None
        except Exception as exc:
            self.health.healthy = False
            self.health.error_message = type(exc).__name__
        self.health.last_check = time.time()
        self.health.latency_ms = (time.perf_counter() - started) * 1000
        return self.health

    async def execute_capability(
        self, capability: Capability, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        candidates = self._capability_tools.get(capability)
        if not candidates:
            raise CapabilityNotSupportedError(
                f"Provider '{self.name}' does not support '{capability.value}'"
            )
        await self.list_tools()
        available = {tool.original_name for tool in self._tools}
        candidate = next((item for item in candidates if item in available), None)
        if candidate is None:
            raise CapabilityNotSupportedError(
                f"Provider '{self.name}' has no upstream operation for '{capability.value}'"
            )
        return await self.call_tool(self._namespaced_name(candidate), arguments)
