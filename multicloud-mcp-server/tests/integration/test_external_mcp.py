"""External MCP-client tests for the stdio boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_external_stdio_client_initializes_discovers_and_calls_native_tool() -> None:
    project = Path(__file__).parents[2]
    config = project / "examples" / "hermes" / "multicloud.semantic.yaml"
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "multicloud_mcp.server", "--config", str(config)],
        env={"PYTHONPATH": str(project / "src")},
    )

    async with stdio_client(server) as (read_stream, write_stream), ClientSession(
        read_stream, write_stream
    ) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert "multicloud__list_providers" in names
            assert "finops__get_cost" in names
            assert "finops__gcp_list_prices" in names
            assert "aws__ec2__describe_instances" not in names

            result = await session.call_tool(
                "finops__compare_list_prices",
                {
                    "service_type": "compute",
                    "region_aws": "us-east-1",
                    "region_azure": "eastus",
                    "specs": {"vcpu": 2, "memory_gb": 4},
                },
            )
            assert result.content
            payload = json.loads(result.content[0].text)
            assert isinstance(payload, dict)

            gcp_result = await session.call_tool(
                "finops__gcp_list_prices", {"service_id": "service-test"}
            )
            assert gcp_result.content
            error_payload = json.loads(gcp_result.content[0].text)
            assert error_payload["error"] == "invalid_request"
