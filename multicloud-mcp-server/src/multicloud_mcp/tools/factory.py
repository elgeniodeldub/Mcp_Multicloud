"""Factory for the built-in native MCP tool catalog."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from multicloud_mcp.finops.services.cost_service import FinOpsCostService
from multicloud_mcp.finops.tools.breakdown import FinOpsBreakdownTool
from multicloud_mcp.finops.tools.compare import FinOpsCompareTool
from multicloud_mcp.finops.tools.get_cost import FinOpsGetCostTool
from multicloud_mcp.health import HealthMonitor
from multicloud_mcp.providers.base import ToolInfo
from multicloud_mcp.router import ProviderRouter
from multicloud_mcp.tools.actual_costs import ActualCostsTool
from multicloud_mcp.tools.compliance import ComplianceCheckerTool
from multicloud_mcp.tools.discover_resources import DiscoverResourcesTool
from multicloud_mcp.tools.list_price_comparison import ListPriceComparisonTool
from multicloud_mcp.tools.list_providers import ListProvidersTool
from multicloud_mcp.tools.registry import NativeToolRegistry, RegisteredNativeTool
from multicloud_mcp.tools.resource_mapper import ResourceMapperTool
from multicloud_mcp.tools.security_posture import SecurityPostureTool


class NativeToolContext:
    """Runtime dependencies available to native tool factories."""

    def __init__(
        self,
        router: ProviderRouter,
        health_monitor: HealthMonitor,
        finops_service: FinOpsCostService,
    ) -> None:
        self.router = router
        self.health_monitor = health_monitor
        self.finops_service = finops_service


ToolBuilder = Callable[[NativeToolContext], RegisteredNativeTool]


def _no_context(tool: Any) -> ToolBuilder:
    def build(_context: NativeToolContext) -> RegisteredNativeTool:
        info: ToolInfo = tool.get_tool_info()
        return RegisteredNativeTool(info, tool.execute)

    return build


def _finops_get_cost(context: NativeToolContext) -> RegisteredNativeTool:
    tool = FinOpsGetCostTool(context.finops_service)
    return RegisteredNativeTool(tool.get_tool_info(), tool.execute)


def _finops_breakdown(context: NativeToolContext) -> RegisteredNativeTool:
    tool = FinOpsBreakdownTool(context.finops_service)
    return RegisteredNativeTool(tool.get_tool_info(), tool.execute)


def _finops_compare(context: NativeToolContext) -> RegisteredNativeTool:
    tool = FinOpsCompareTool(context.finops_service)
    return RegisteredNativeTool(tool.get_tool_info(), tool.execute)


def _list_providers(context: NativeToolContext) -> RegisteredNativeTool:
    tool = ListProvidersTool()

    async def execute(arguments: dict[str, Any]) -> dict[str, Any]:
        return await tool.execute(arguments, context.router, context.health_monitor)

    return RegisteredNativeTool(tool.get_tool_info(), execute)


def _discover_resources(context: NativeToolContext) -> RegisteredNativeTool:
    tool = DiscoverResourcesTool()

    async def execute(arguments: dict[str, Any]) -> dict[str, Any]:
        return await tool.execute(arguments, context.router)

    return RegisteredNativeTool(tool.get_tool_info(), execute)


def _security_posture(context: NativeToolContext) -> RegisteredNativeTool:
    tool = SecurityPostureTool()

    async def execute(arguments: dict[str, Any]) -> dict[str, Any]:
        return await tool.execute(arguments, context.router)

    return RegisteredNativeTool(tool.get_tool_info(), execute)


def _compliance(context: NativeToolContext) -> RegisteredNativeTool:
    tool = ComplianceCheckerTool()

    async def execute(arguments: dict[str, Any]) -> dict[str, Any]:
        return await tool.execute(arguments, context.router)

    return RegisteredNativeTool(tool.get_tool_info(), execute)


def build_native_tool_registry(
    context: NativeToolContext, enabled: list[str]
) -> NativeToolRegistry:
    """Build the configured native tool registry."""
    builders: dict[str, ToolBuilder] = {
        "get_cost": _finops_get_cost,
        "breakdown": _finops_breakdown,
        "compare": _finops_compare,
        "actual_costs": _no_context(ActualCostsTool()),
        "list_price_comparison": _no_context(ListPriceComparisonTool()),
        "resource_mapper": _no_context(ResourceMapperTool()),
        "list_providers": _list_providers,
        "discover_resources": _discover_resources,
        "security_posture": _security_posture,
        "compliance_checker": _compliance,
    }
    registry = NativeToolRegistry()
    for key in enabled:
        builder = builders.get(key)
        if builder is not None:
            registry.register(builder(context))
    return registry
