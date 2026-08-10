"""Abstract base class for upstream MCP provider adapters."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class ProviderHealth:
    """Health status of a provider."""

    healthy: bool = False
    last_check: float = field(default_factory=lambda: 0.0)
    error_message: str | None = None
    tools_count: int = 0
    latency_ms: float = 0.0


@dataclass
class ToolInfo:
    """Information about a tool from an upstream provider."""

    name: str
    description: str
    input_schema: dict[str, Any]
    original_name: str
    provider: str
    namespace: str


class ProviderAdapter(ABC):
    """Abstract adapter for connecting to upstream MCP servers."""

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
    ) -> None:
        self.name = name
        self.namespace = namespace
        self.command = command
        self.args = args
        self.env = env
        self.timeout = timeout
        self.max_concurrency = max_concurrency
        self.retry_attempts = retry_attempts
        self.circuit_failure_threshold = circuit_failure_threshold
        self.circuit_recovery_timeout = circuit_recovery_timeout
        self.health = ProviderHealth()
        self._tools: list[ToolInfo] = []
        self._lock = asyncio.Lock()
        self._logger = logger.bind(provider=name, namespace=namespace)

    @property
    def tools(self) -> list[ToolInfo]:
        """Return cached tools list."""
        return self._tools

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the upstream MCP server."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the upstream MCP server."""

    @abstractmethod
    async def list_tools(self) -> list[ToolInfo]:
        """List available tools from the upstream server."""

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the upstream server."""

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Perform a health check on the provider."""

    def _namespaced_name(self, original_name: str) -> str:
        """Convert original tool name to namespaced name."""
        return f"{self.namespace}__{original_name}"

    def _original_name(self, namespaced_name: str) -> str:
        """Convert namespaced name back to original tool name."""
        prefix = f"{self.namespace}__"
        if namespaced_name.startswith(prefix):
            return namespaced_name[len(prefix) :]
        return namespaced_name

    @property
    def capabilities(self) -> set[Any]:
        """Semantic capabilities declared by this provider adapter."""
        return set(getattr(self, "_capability_tools", {}))

    def supports(self, capability: Any) -> bool:
        """Return whether this provider exposes a semantic capability."""
        return capability in self.capabilities

    async def execute_capability(
        self, capability: Any, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a declared capability through the provider adapter."""
        raise NotImplementedError("Provider does not implement semantic capabilities")
