"""Tests for the provider router."""

import pytest

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo
from multicloud_mcp.router import ProviderRouter, ToolNotFoundError


class MockProvider(ProviderAdapter):
    """Mock provider for testing."""

    def __init__(self, name: str, tools: list[ToolInfo] | None = None):
        super().__init__(name, name, "echo", [], {})
        self._mock_tools = tools or []

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def list_tools(self):
        return self._mock_tools

    async def call_tool(self, name, args):
        return {"content": [{"type": "text", "text": "ok"}], "isError": False}

    async def health_check(self):
        return ProviderHealth(healthy=True)


@pytest.mark.asyncio
async def test_router_register_provider():
    router = ProviderRouter()
    provider = MockProvider("aws")
    router.register_provider(provider)
    assert "aws" in router.providers


@pytest.mark.asyncio
async def test_router_refresh_tools():
    router = ProviderRouter()
    tools = [ToolInfo("aws__s3__list", "List S3", {}, "list", "aws", "aws")]
    provider = MockProvider("aws", tools)
    router.register_provider(provider)

    result = await router.refresh_tools(force=True)
    assert len(result) == 1
    assert result[0].name == "aws__s3__list"


@pytest.mark.asyncio
async def test_router_call_tool_not_found():
    router = ProviderRouter()
    with pytest.raises(ToolNotFoundError):
        await router.call_tool("nonexistent__tool", {})


@pytest.mark.asyncio
async def test_router_call_tool_success():
    router = ProviderRouter()
    tools = [ToolInfo("aws__test", "Test", {}, "test", "aws", "aws")]
    provider = MockProvider("aws", tools)
    router.register_provider(provider)
    await router.refresh_tools(force=True)

    result = await router.call_tool("aws__test", {})
    assert result["isError"] is False
