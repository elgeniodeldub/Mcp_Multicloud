"""Discover resources across all connected clouds."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from multicloud_mcp.providers.base import ToolInfo
from multicloud_mcp.providers.capabilities import Capability

logger = structlog.get_logger()

RESOURCE_CAPABILITIES = {
    "kubernetes": Capability.KUBERNETES,
    "compute": Capability.COMPUTE,
    "storage": Capability.STORAGE,
    "database": Capability.DATABASE,
}

LEGACY_CAPABILITY_SUFFIXES = {
    Capability.KUBERNETES: ("list_clusters",),
    Capability.COMPUTE: ("describe_instances", "list_virtual_machines"),
    Capability.STORAGE: ("list_buckets", "list_storage_accounts"),
    Capability.DATABASE: ("describe_db_instances", "list_servers"),
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
        resource_types = arguments.get("resource_types") or list(RESOURCE_CAPABILITIES)
        resources: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []

        async def discover_provider(
            provider_name: str,
        ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
            provider_resources: list[dict[str, Any]] = []
            provider_errors: list[dict[str, str]] = []
            if provider_name not in router.providers:
                return [], [{"provider": provider_name, "error": "Provider not connected"}]
            provider = router.providers[provider_name]
            for resource_type in resource_types:
                capability = RESOURCE_CAPABILITIES.get(resource_type)
                if capability is None:
                    provider_errors.append(
                        {
                            "provider": provider_name,
                            "resource_type": resource_type,
                            "error": "Unsupported resource type",
                        }
                    )
                    continue
                try:
                    execute_capability = getattr(provider, "execute_capability", None)
                    supports = getattr(provider, "supports", None)
                    if callable(execute_capability) and callable(supports) and supports(capability):
                        result = await execute_capability(capability, {})
                        tool_name = capability.value
                    else:
                        available = {tool.original_name for tool in provider.tools}
                        suffix = next(
                            (
                                item
                                for item in LEGACY_CAPABILITY_SUFFIXES[capability]
                                if any(name.endswith(item) for name in available)
                            ),
                            None,
                        )
                        if suffix is None:
                            raise RuntimeError("Capability not supported")
                        tool_name = next(
                            f"{provider_name}__{name}"
                            for name in available
                            if name.endswith(suffix)
                        )
                        result = await router.call_tool(tool_name, {})
                    if isinstance(result, dict) and result.get("isError"):
                        raise RuntimeError(str(result.get("content", "tool error")))
                    provider_resources.append(
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
                    provider_errors.append(
                        {
                            "provider": provider_name,
                            "resource_type": resource_type,
                            "error": str(exc),
                        }
                    )
            return provider_resources, provider_errors

        results = await asyncio.gather(
            *(discover_provider(provider_name) for provider_name in selected)
        )
        for provider_resources, provider_errors in results:
            resources.extend(provider_resources)
            errors.extend(provider_errors)
        return {"resources": resources, "errors": errors, "count": len(resources)}
