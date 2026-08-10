"""Routing engine for namespaced tool calls across providers."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo

logger = structlog.get_logger()


class RouterError(Exception):
    """Base exception for routing errors."""


class ProviderNotFoundError(RouterError):
    """Raised when no provider can handle a tool."""


class ToolNotFoundError(RouterError):
    """Raised when a tool is not found in any provider."""


class ProviderRouter:
    """Routes tool calls to the appropriate upstream provider."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderAdapter] = {}
        self._tools_index: dict[str, ToolInfo] = {}
        self._provider_by_tool: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._logger = logger.bind(component="router")
        self._last_refresh: float = 0.0
        self._cache_ttl: float = 300.0

    def register_provider(self, provider: ProviderAdapter) -> None:
        """Register a provider adapter."""
        self._providers[provider.name] = provider
        self._logger.info("provider_registered", name=provider.name, namespace=provider.namespace)

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider adapter."""
        if name in self._providers:
            del self._providers[name]
            self._logger.info("provider_unregistered", name=name)

    @property
    def providers(self) -> dict[str, ProviderAdapter]:
        """Return registered providers."""
        return self._providers

    @property
    def all_tools(self) -> list[ToolInfo]:
        """Return all available tools from all providers."""
        return list(self._tools_index.values())

    async def refresh_tools(self, force: bool = False) -> list[ToolInfo]:
        """Refresh the tools catalog from all providers."""
        async with self._lock:
            now = time.time()
            if not force and (now - self._last_refresh) < self._cache_ttl:
                return self.all_tools

            self._tools_index.clear()
            self._provider_by_tool.clear()

            tasks = []
            for _name, provider in self._providers.items():
                tasks.append(self._safe_list_tools(provider))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for provider_name, tools in zip(self._providers.keys(), results, strict=True):
                if isinstance(tools, BaseException):
                    self._logger.warning(
                        "provider_tools_refresh_failed",
                        provider=provider_name,
                        error=str(tools),
                    )
                    continue

                for tool in tools:
                    self._tools_index[tool.name] = tool
                    self._provider_by_tool[tool.name] = provider_name

            self._last_refresh = time.time()
            self._logger.info(
                "tools_catalog_refreshed",
                total_tools=len(self._tools_index),
                providers=len(self._providers),
            )

            return self.all_tools

    async def _safe_list_tools(self, provider: ProviderAdapter) -> list[ToolInfo]:
        """Safely list tools from a provider with error handling."""
        try:
            return await provider.list_tools()
        except Exception as e:
            self._logger.warning(
                "safe_list_tools_failed",
                provider=provider.name,
                error=str(e),
            )
            return []

    def get_tool_info(self, tool_name: str) -> ToolInfo | None:
        """Get information about a specific tool."""
        return self._tools_index.get(tool_name)

    def get_provider_for_tool(self, tool_name: str) -> ProviderAdapter | None:
        """Get the provider that handles a specific tool."""
        provider_name = self._provider_by_tool.get(tool_name)
        if provider_name:
            return self._providers.get(provider_name)
        return None

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a tool call to the appropriate provider."""
        await self.refresh_tools()

        provider = self.get_provider_for_tool(tool_name)

        if not provider:
            if tool_name.startswith("multicloud__"):
                raise ToolNotFoundError(
                    f"Multicloud tool '{tool_name}' not found. "
                    "Native tools must be registered separately."
                )

            available = [t for t in self._tools_index if tool_name.split("__")[-1] in t]
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found. Did you mean one of: {available[:5]}?"
            )

        self._logger.info(
            "routing_tool_call",
            tool=tool_name,
            provider=provider.name,
        )

        return await provider.call_tool(tool_name, arguments)

    async def health_check_all(self) -> dict[str, ProviderHealth]:
        """Run health checks on all providers."""
        results = {}
        tasks = []

        for _name, provider in self._providers.items():
            tasks.append(self._safe_health_check(provider))

        health_results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, health in zip(self._providers.keys(), health_results, strict=True):
            if isinstance(health, BaseException):
                results[name] = ProviderHealth(
                    healthy=False,
                    error_message=str(health),
                )
            else:
                results[name] = health

        return results

    async def _safe_health_check(self, provider: ProviderAdapter) -> ProviderHealth:
        """Safely run health check with timeout."""
        try:
            return await asyncio.wait_for(
                provider.health_check(),
                timeout=provider.timeout,
            )
        except TimeoutError:
            return ProviderHealth(
                healthy=False,
                error_message="Health check timeout",
            )
        except Exception as e:
            return ProviderHealth(
                healthy=False,
                error_message=str(e),
            )
