"""List providers and their health status."""

from __future__ import annotations

from typing import Any

import structlog

from multicloud_mcp.providers.base import ToolInfo

logger = structlog.get_logger()


class ListProvidersTool:
    """List all connected providers and their health status."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__list_providers",
            description="List all connected cloud providers, their health status, latency, and available tools count.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            original_name="multicloud__list_providers",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(
        self, arguments: dict[str, Any], router: Any, health_monitor: Any
    ) -> dict[str, Any]:
        """Execute list providers. Requires router and health_monitor injected."""
        health = await router.health_check_all()
        providers: list[dict[str, Any]] = []
        for name, provider in router.providers.items():
            status = health.get(name, provider.health)
            breaker = health_monitor._breakers.get(name)
            providers.append(
                {
                    "name": name,
                    "healthy": status.healthy,
                    "tools_count": len(provider.tools) or status.tools_count,
                    "latency_ms": status.latency_ms,
                    "circuit_state": breaker.state.value if breaker else "unknown",
                }
            )
        logger.info("providers_listed", count=len(providers))
        return {"providers": providers, "count": len(providers)}
