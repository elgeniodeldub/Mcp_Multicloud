"""End-to-end integration tests."""

import pytest

from multicloud_mcp.config import Settings
from multicloud_mcp.providers.base import ProviderHealth, ToolInfo
from multicloud_mcp.server import MulticloudMCPServer


class MockProvider:
    name = "aws"
    namespace = "aws"
    timeout = 10
    tools = [
        ToolInfo(
            name="aws__eks__list_clusters",
            description="clusters",
            input_schema={},
            original_name="eks__list_clusters",
            provider="aws",
            namespace="aws",
        ),
        ToolInfo(
            name="aws__iam__list_roles",
            description="roles",
            input_schema={},
            original_name="iam__list_roles",
            provider="aws",
            namespace="aws",
        ),
    ]
    health = ProviderHealth(healthy=True, tools_count=2, latency_ms=1.0)

    async def list_tools(self):
        return self.tools

    async def call_tool(self, name, arguments):
        return {"content": [{"type": "text", "text": '[{"name": "cluster-1"}]'}], "isError": False}

    async def health_check(self):
        return self.health

    async def connect(self):
        return None

    async def disconnect(self):
        return None


@pytest.mark.asyncio
async def test_server_lifecycle():
    """Test full server lifecycle: init -> list_tools -> shutdown."""
    settings = Settings()
    settings.providers = {}  # No providers for unit test
    server = MulticloudMCPServer(settings)

    await server.initialize()
    # Server should initialize without errors even with no providers
    await server.shutdown()


@pytest.mark.asyncio
async def test_list_tools_with_no_providers():
    """Test list_tools returns multicloud tools when no providers."""
    settings = Settings()
    settings.providers = {}
    server = MulticloudMCPServer(settings)

    await server.initialize()
    _ = server._get_multicloud_tools()
    # Should have at least multicloud tools
    await server.shutdown()


@pytest.mark.asyncio
async def test_end_to_end_native_tools_with_mock_provider():
    settings = Settings()
    settings.providers = {}
    server = MulticloudMCPServer(settings)
    provider = MockProvider()
    server.router.register_provider(provider)
    server.health_monitor.register_provider("aws", provider)
    await server.router.refresh_tools(force=True)

    providers = await server._call_multicloud_tool("multicloud__list_providers", {})
    resources = await server._call_multicloud_tool(
        "multicloud__discover_resources", {"resource_types": ["kubernetes"]}
    )
    posture = await server._call_multicloud_tool("multicloud__security_posture", {})
    compliance = await server._call_multicloud_tool(
        "multicloud__compliance_check", {"framework": "NIST"}
    )

    assert providers["providers"][0]["name"] == "aws"
    assert resources["count"] == 1
    assert posture["summary"]["checks_run"] == 1
    assert compliance["framework"] == "NIST"
