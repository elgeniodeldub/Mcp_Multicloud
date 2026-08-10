"""Tests for multicloud native tools."""

import pytest

from multicloud_mcp.tools.cost_comparison import CostComparisonTool
from multicloud_mcp.tools.resource_mapper import ResourceMapperTool
from multicloud_mcp.tools.list_providers import ListProvidersTool
from multicloud_mcp.tools.discover_resources import DiscoverResourcesTool
from multicloud_mcp.tools.security_posture import SecurityPostureTool
from multicloud_mcp.tools.compliance import ComplianceCheckerTool
from multicloud_mcp.providers.base import ProviderHealth, ToolInfo


@pytest.mark.asyncio
async def test_cost_comparison_compute():
    tool = CostComparisonTool()
    result = await tool.execute({
        "service_type": "compute",
        "region_aws": "us-east-1",
        "region_azure": "eastus",
        "specs": {"vcpu": 4, "memory_gb": 16},
    })
    assert "comparison" in result
    assert "aws" in result["comparison"]
    assert "azure" in result["comparison"]
    assert "savings" in result["comparison"]


@pytest.mark.asyncio
async def test_cost_comparison_storage():
    tool = CostComparisonTool()
    result = await tool.execute({
        "service_type": "storage",
        "region_aws": "us-east-1",
        "region_azure": "eastus",
        "specs": {"storage_gb": 1000, "storage_type": "ssd"},
    })
    assert result["comparison"]["aws"]["service"] == "EBS gp3"


@pytest.mark.asyncio
async def test_resource_mapper_aws_to_azure():
    tool = ResourceMapperTool()
    result = await tool.execute({
        "source_provider": "aws",
        "resource_type": "s3_bucket",
        "target_provider": "azure",
    })
    assert result["equivalent"] == "Azure Blob Storage"
    assert result["mapping_confidence"] == "high"


@pytest.mark.asyncio
async def test_resource_mapper_azure_to_aws():
    tool = ResourceMapperTool()
    result = await tool.execute({
        "source_provider": "azure",
        "resource_type": "aks_cluster",
        "target_provider": "aws",
    })
    assert result["equivalent"] == "Amazon EKS"


@pytest.mark.asyncio
async def test_resource_mapper_unknown():
    tool = ResourceMapperTool()
    result = await tool.execute({
        "source_provider": "aws",
        "resource_type": "unknown_resource",
        "target_provider": "azure",
    })
    assert result["mapping_confidence"] == "low"
    assert "No direct equivalent" in result["equivalent"]


class FakeProvider:
    def __init__(self, name: str, tools: list[str]) -> None:
        self.name = name
        self.tools = [ToolInfo(name=tool, description="", input_schema={},
                               original_name=tool.split("__", 1)[-1], provider=name,
                               namespace=name) for tool in tools]
        self.health = ProviderHealth(healthy=True, tools_count=len(tools), latency_ms=4.2)


class FakeRouter:
    def __init__(self) -> None:
        self.providers = {
            "aws": FakeProvider("aws", ["aws__eks__list_clusters", "aws__iam__list_roles"]),
            "azure": FakeProvider("azure", ["azure__aks__list_clusters"]),
        }

    async def health_check_all(self):
        return {name: provider.health for name, provider in self.providers.items()}

    async def call_tool(self, name, arguments):
        return {"content": [{"type": "text", "text": "[{\"name\": \"demo\"}]"}], "isError": False}


class FakeHealthMonitor:
    def __init__(self) -> None:
        from multicloud_mcp.health import CircuitBreaker
        self._breakers = {"aws": CircuitBreaker(), "azure": CircuitBreaker()}


@pytest.mark.asyncio
async def test_list_providers_reports_health_and_circuit():
    result = await ListProvidersTool().execute({}, FakeRouter(), FakeHealthMonitor())
    assert result["count"] == 2
    assert result["providers"][0]["circuit_state"] == "closed"


@pytest.mark.asyncio
async def test_discover_resources_unifies_provider_results():
    result = await DiscoverResourcesTool().execute(
        {"resource_types": ["kubernetes"]}, FakeRouter()
    )
    assert result["count"] == 2
    assert {item["provider"] for item in result["resources"]} == {"aws", "azure"}


@pytest.mark.asyncio
async def test_security_and_compliance_use_provider_tools():
    router = FakeRouter()
    posture = await SecurityPostureTool().execute({}, router)
    compliance = await ComplianceCheckerTool().execute({"framework": "CIS"}, router)
    assert posture["summary"]["checks_run"] == 1
    assert compliance["framework"] == "CIS"
    assert compliance["status"] == "evaluated"
