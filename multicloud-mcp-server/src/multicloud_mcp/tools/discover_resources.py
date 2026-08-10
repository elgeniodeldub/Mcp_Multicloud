"""Discover resources across all connected clouds."""

from __future__ import annotations

from typing import Any

import structlog

from multicloud_mcp.providers.base import ToolInfo

logger = structlog.get_logger()

RESOURCE_TOOLS = {
    "kubernetes": ("eks__list_clusters", "aks__list_clusters", "list_clusters"),
    "compute": (
        "ec2__describe_instances",
        "compute__list_virtual_machines",
        "list_virtual_machines",
    ),
    "storage": ("s3__list_buckets", "storage__list_storage_accounts", "list_storage_accounts"),
    "database": ("rds__describe_db_instances", "database__list_servers", "list_servers"),
}


def _payload(result: Any) -> Any:
    """Extract useful data from a normalized router response."""
    if not isinstance(result, dict):
        return result
    content = result.get("content", result)
    if isinstance(content, list):
        values = []
        for item in content:
            value = item.get("text") if isinstance(item, dict) else item
            if isinstance(value, str):
                try:
                    import json

                    value = json.loads(value)
                except (TypeError, ValueError):
                    pass
            values.append(value)
        return values[0] if len(values) == 1 else values
    return content


class DiscoverResourcesTool:
    """Discover active resources across all connected cloud providers."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__discover_resources",
            description="Discover all active resources across connected AWS and Azure accounts.",
            input_schema={
                "type": "object",
                "properties": {
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                    "resource_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["kubernetes", "compute", "storage", "database"],
                        },
                    },
                },
            },
            original_name="multicloud__discover_resources",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any], router: Any) -> dict[str, Any]:
        """Execute discover resources. Requires router injected."""
        selected = arguments.get("providers") or list(router.providers)
        resource_types = arguments.get("resource_types") or list(RESOURCE_TOOLS)
        resources: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for provider_name in selected:
            if provider_name not in router.providers:
                errors.append({"provider": provider_name, "error": "Provider not connected"})
                continue
            available = {tool.name for tool in router.providers[provider_name].tools}
            for resource_type in resource_types:
                candidates = RESOURCE_TOOLS.get(resource_type, ())
                tool_name = next(
                    (
                        f"{provider_name}__{candidate}"
                        for candidate in candidates
                        if f"{provider_name}__{candidate}" in available
                    ),
                    None,
                )
                if tool_name is None:
                    errors.append(
                        {
                            "provider": provider_name,
                            "resource_type": resource_type,
                            "error": "No listing tool available",
                        }
                    )
                    continue
                try:
                    result = await router.call_tool(tool_name, {})
                    if isinstance(result, dict) and result.get("isError"):
                        raise RuntimeError(str(result.get("content", "tool error")))
                    resources.append(
                        {
                            "provider": provider_name,
                            "resource_type": resource_type,
                            "data": _payload(result),
                        }
                    )
                except Exception as exc:
                    logger.warning(
                        "resource_discovery_failed",
                        provider=provider_name,
                        resource_type=resource_type,
                        error=str(exc),
                    )
                    errors.append(
                        {
                            "provider": provider_name,
                            "resource_type": resource_type,
                            "error": str(exc),
                        }
                    )
        return {"resources": resources, "errors": errors, "count": len(resources)}
