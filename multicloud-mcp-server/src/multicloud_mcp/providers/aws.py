"""AWS provider identity and semantic capability declarations."""

from __future__ import annotations

from multicloud_mcp.providers.capabilities import Capability
from multicloud_mcp.providers.mcp import MCPProviderAdapter
from multicloud_mcp.providers.transport import ProviderTransport


class AWSProvider(MCPProviderAdapter):
    """AWS adapter backed by the official AWS MCP server."""

    _capability_tools = {
        Capability.COMPUTE: ("ec2__describe_instances",),
        Capability.STORAGE: ("s3__list_buckets",),
        Capability.DATABASE: ("rds__describe_db_instances",),
        Capability.KUBERNETES: ("eks__list_clusters",),
        Capability.SECURITY: (
            "iam__get_account_authorization_details",
            "iam__list_roles",
        ),
    }

    def __init__(
        self,
        command: str = "uvx",
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
            name="aws",
            namespace="aws",
            command=command,
            args=args or ["awslabs.core-mcp-server@1.0.27"],
            env=env or {},
            timeout=timeout,
            max_concurrency=max_concurrency,
            retry_attempts=retry_attempts,
            circuit_failure_threshold=circuit_failure_threshold,
            circuit_recovery_timeout=circuit_recovery_timeout,
            transport=transport,
        )
