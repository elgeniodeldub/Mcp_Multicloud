"""Application execution contracts and exposure policy tests."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from multicloud_mcp.application.context import ExecutionContext
from multicloud_mcp.application.results import ApplicationError, ToolExecutionResult
from multicloud_mcp.config import Settings
from multicloud_mcp.providers.base import ToolInfo, ToolSafety
from multicloud_mcp.server import MulticloudMCPServer
from multicloud_mcp.tools.registry import RegisteredNativeTool


def test_execution_context_excludes_sensitive_metadata() -> None:
    context = ExecutionContext.from_arguments(
        "request-1",
        {"providers": ["aws"], "metadata": {"team": "finops", "token": "hidden"}},
        "http",
    )
    assert context.providers == ("aws",)
    assert context.metadata == {"team": "finops"}
    assert "hidden" not in repr(context)


def test_tool_execution_result_serializes_stable_errors() -> None:
    result = ToolExecutionResult(
        errors=[ApplicationError("timeout", "Tool execution timed out", "aws")],
        partial=True,
        request_id="request-1",
    )
    payload = result.to_dict()
    assert payload["errors"][0]["code"] == "timeout"
    assert result.legacy_data()["error"] == "timeout"


def test_native_tool_metadata_is_read_only_by_default() -> None:
    async def execute(_: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(0)
        return {"ok": True}

    tool = RegisteredNativeTool(
        ToolInfo("finops__test", "read only", {}, "finops__test", "finops", "finops"),
        execute,
    )
    assert tool.get_tool_info().safety is ToolSafety.READ_ONLY


def test_provider_passthrough_visibility_is_configurable() -> None:
    server = MulticloudMCPServer(Settings())
    assert server._tool_exposed("aws__ec2__describe_instances")
    server.settings.tool_exposure.provider_passthrough = False
    assert not server._tool_exposed("aws__ec2__describe_instances")
    assert server._tool_exposed("finops__gcp_list_prices")


@pytest.mark.asyncio
async def test_stdio_and_http_share_application_executor() -> None:
    server = MulticloudMCPServer(Settings())
    assert server.tool_executor.native_tools is server.native_tools
    await server.shutdown()
