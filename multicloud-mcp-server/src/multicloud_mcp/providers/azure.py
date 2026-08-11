"""Azure provider identity and semantic capability declarations."""

from __future__ import annotations

from multicloud_mcp.providers.capabilities import Capability
from multicloud_mcp.providers.mcp import MCPProviderAdapter
from multicloud_mcp.providers.transport import ProviderTransport


class AzureProvider(MCPProviderAdapter):
    """Azure adapter backed by the official Azure MCP server."""

    _capability_tools = {
        Capability.COMPUTE: ("compute__list_virtual_machines", "list_virtual_machines"),
        Capability.STORAGE: ("storage__list_storage_accounts", "list_storage_accounts"),
        Capability.DATABASE: ("database__list_servers", "list_servers"),
        Capability.KUBERNETES: ("aks__list_clusters", "list_clusters"),
        Capability.SECURITY: (
            "authorization__list_role_assignments",
            "security__list_findings",
        ),
    }

    def __init__(
        self,
        command: str = "npx",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 60,
        max_concurrency: int = 10,
        retry_attempts: int = 2,
        circuit_failure_threshold: int = 5,
        circuit_recovery_timeout: float = 30.0,
        transport: ProviderTransport | None = None,
    ) -> None:
        super().__init__(
            name="azure",
            namespace="azure",
            command=command,
            args=args or ["-y", "@azure/mcp@2.0.4", "server", "start"],
            env=env or {},
            timeout=timeout,
            max_concurrency=max_concurrency,
            retry_attempts=retry_attempts,
            circuit_failure_threshold=circuit_failure_threshold,
            circuit_recovery_timeout=circuit_recovery_timeout,
            transport=transport,
        )
