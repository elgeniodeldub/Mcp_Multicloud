"""Tests for native tool and provider registration."""

from __future__ import annotations

import pytest

from multicloud_mcp.config import ProviderConfig, Settings
from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo
from multicloud_mcp.providers.registry import (
    DisabledProviderError,
    DuplicateProviderError,
    ProviderRegistry,
    UnknownProviderError,
    build_provider_registry,
)
from multicloud_mcp.server import MulticloudMCPServer
from multicloud_mcp.tools.factory import NativeToolContext, build_native_tool_registry
from multicloud_mcp.tools.registry import (
    DuplicateToolError,
    NativeToolNotFoundError,
    NativeToolRegistry,
    RegisteredNativeTool,
)


async def _execute(_arguments: dict[str, object]) -> dict[str, object]:
    return {"ok": True}


def _tool(name: str) -> RegisteredNativeTool:
    return RegisteredNativeTool(
        ToolInfo(name, "test", {}, name, "multicloud", "multicloud"), _execute
    )


def test_tool_registry_registration_lookup_and_duplicates() -> None:
    registry = NativeToolRegistry()
    tool = _tool("multicloud__test")
    registry.register(tool)
    assert registry.get("multicloud__test") is tool
    assert registry.list_tools()[0].name == "multicloud__test"
    with pytest.raises(DuplicateToolError):
        registry.register(_tool("multicloud__test"))
    with pytest.raises(NativeToolNotFoundError):
        registry.get("multicloud__missing")


class FactoryProvider(ProviderAdapter):
    def __init__(self, name: str) -> None:
        super().__init__(name, name, "test", [], {})

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def list_tools(self) -> list[ToolInfo]:
        return []

    async def call_tool(self, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        return {"content": [], "isError": False}

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(healthy=True)


def _provider_config() -> ProviderConfig:
    return ProviderConfig(command="test", namespace="test")


def test_provider_registry_registration_creation_and_unknown() -> None:
    registry = ProviderRegistry()
    registry.register("test", lambda _config: FactoryProvider("test"))
    provider = registry.create("TEST", _provider_config())
    assert provider.name == "test"
    assert registry.supports("test")
    with pytest.raises(DuplicateProviderError):
        registry.register("test", lambda _config: FactoryProvider("test"))
    with pytest.raises(UnknownProviderError):
        registry.create("missing", _provider_config())


def test_provider_registry_respects_disabled_configuration() -> None:
    registry = build_provider_registry()
    config = _provider_config().model_copy(update={"enabled": False})
    with pytest.raises(DisabledProviderError):
        registry.create("aws", config)


def test_default_native_registry_respects_enabled_tools() -> None:
    server = MulticloudMCPServer(Settings())
    context = NativeToolContext(server.router, server.health_monitor, server.finops_service)
    registry = build_native_tool_registry(context, ["resource_mapper"])
    assert registry.get("multicloud__map_resource").name == "multicloud__map_resource"
    with pytest.raises(NativeToolNotFoundError):
        registry.get("multicloud__list_providers")


def test_default_native_registry_includes_gcp_list_prices() -> None:
    server = MulticloudMCPServer(Settings())
    context = NativeToolContext(server.router, server.health_monitor, server.finops_service)
    registry = build_native_tool_registry(context, ["gcp_list_prices"])
    assert registry.get("finops__gcp_list_prices").name == "finops__gcp_list_prices"


def test_server_initializes_registries_without_connecting_providers() -> None:
    server = MulticloudMCPServer(Settings())
    assert server.provider_registry.supports("aws")
    assert server.provider_registry.supports("azure")
    assert "finops__get_cost" in {tool.name for tool in server.native_tools.list_tools()}


@pytest.mark.asyncio
async def test_server_shutdown_without_connected_providers() -> None:
    server = MulticloudMCPServer(Settings())
    await server.shutdown()
