"""Tests for the FinOps Framework playbook catalog and its MCP tool."""

from __future__ import annotations

from typing import Any

import pytest

from multicloud_mcp.config import Settings
from multicloud_mcp.finops.exceptions import InvalidPlaybookRequestError
from multicloud_mcp.finops.playbooks import (
    FINOPS_DOMAINS,
    FINOPS_PHASES,
    Playbook,
    PlaybookCatalog,
    PlaybookFormatError,
    load_default_catalog,
)
from multicloud_mcp.finops.tools.playbooks import FinOpsPlaybooksTool
from multicloud_mcp.providers.base import ToolSafety
from multicloud_mcp.server import MulticloudMCPServer
from multicloud_mcp.tools.factory import NativeToolContext, build_native_tool_registry

EXPECTED_PLAYBOOKS = {
    "cost-allocation-tagging",
    "anomaly-management",
    "budgeting-and-forecasting",
    "rightsizing-compute",
    "idle-and-orphaned-resources",
    "commitment-based-discounts",
    "storage-optimization",
    "unit-economics",
    "showback-and-chargeback",
    "policy-and-governance",
}

VALID_DOC = """---
id: sample-playbook
title: Sample playbook
summary: A short summary.
domain: Optimize Usage & Cost
capabilities: [Workload Optimization]
phases: [optimize]
providers: [aws, azure]
related_tools: [finops__get_cost]
tags: [idle, waste]
---
# Sample playbook

Body text about idle virtual machines.
"""


def _catalog_from(*docs: str) -> PlaybookCatalog:
    return PlaybookCatalog.from_documents({f"doc{i}.md": doc for i, doc in enumerate(docs)})


def _native_tool_names() -> set[str]:
    server = MulticloudMCPServer(Settings())
    return {tool.name for tool in server.native_tools.list_tools()}


# --- catalog -----------------------------------------------------------------


def test_default_catalog_ships_common_framework_playbooks() -> None:
    catalog = load_default_catalog()
    assert {playbook.id for playbook in catalog.all()} == EXPECTED_PLAYBOOKS


def test_default_catalog_covers_every_framework_domain() -> None:
    catalog = load_default_catalog()
    assert {playbook.domain for playbook in catalog.all()} == set(FINOPS_DOMAINS)


def test_default_playbooks_only_reference_registered_native_tools() -> None:
    names = _native_tool_names()
    for playbook in load_default_catalog().all():
        unknown = set(playbook.related_tools) - names
        assert not unknown, f"{playbook.id} references unknown tools: {unknown}"


def test_default_playbooks_have_required_sections() -> None:
    for playbook in load_default_catalog().all():
        assert playbook.phases and set(playbook.phases) <= set(FINOPS_PHASES)
        assert playbook.capabilities
        for heading in ("## When to use", "## Steps", "## KPIs", "## Pitfalls"):
            assert heading in playbook.body, f"{playbook.id} is missing '{heading}'"


def test_catalog_parses_front_matter() -> None:
    playbook = _catalog_from(VALID_DOC).get("sample-playbook")
    assert isinstance(playbook, Playbook)
    assert playbook.title == "Sample playbook"
    assert playbook.domain == "Optimize Usage & Cost"
    assert playbook.providers == ("aws", "azure")
    assert playbook.body.startswith("# Sample playbook")


@pytest.mark.parametrize(
    ("broken", "message"),
    [
        ("# no front matter", "front matter"),
        (VALID_DOC.replace("domain: Optimize Usage & Cost", "domain: Nope"), "domain"),
        (VALID_DOC.replace("phases: [optimize]", "phases: [later]"), "phase"),
        (VALID_DOC.replace("id: sample-playbook", "id: ../etc/passwd"), "id"),
        (VALID_DOC.replace("title: Sample playbook\n", ""), "title"),
    ],
)
def test_catalog_rejects_invalid_documents(broken: str, message: str) -> None:
    with pytest.raises(PlaybookFormatError, match=message):
        _catalog_from(broken)


def test_catalog_rejects_duplicate_ids() -> None:
    with pytest.raises(PlaybookFormatError, match="duplicate"):
        _catalog_from(VALID_DOC, VALID_DOC)


def test_search_ranks_title_and_tag_matches_first() -> None:
    other = (
        VALID_DOC.replace("sample-playbook", "other")
        .replace("Sample playbook", "Other")
        .replace("[idle, waste]", "[budget]")
        .replace("idle virtual machines", "budgets and idle notes")
    )
    catalog = _catalog_from(VALID_DOC, other)
    results = catalog.search("idle")
    assert [playbook.id for playbook, _score in results] == ["sample-playbook", "other"]


def test_search_returns_nothing_for_unrelated_query() -> None:
    assert _catalog_from(VALID_DOC).search("kubernetes") == []


# --- MCP tool ----------------------------------------------------------------


@pytest.fixture
def tool() -> FinOpsPlaybooksTool:
    return FinOpsPlaybooksTool(load_default_catalog())


def test_tool_info_is_read_only_finops_tool(tool: FinOpsPlaybooksTool) -> None:
    info = tool.get_tool_info()
    assert info.name == "finops__playbooks"
    assert info.namespace == "finops"
    assert info.safety is ToolSafety.READ_ONLY
    assert info.input_schema["properties"]["action"]["enum"] == ["list", "search", "get"]


async def test_list_returns_summaries_without_bodies(tool: FinOpsPlaybooksTool) -> None:
    result = await tool.execute({})
    assert result["action"] == "list"
    assert result["content_type"] == "guidance"
    assert result["returned_count"] == len(EXPECTED_PLAYBOOKS)
    assert all("body" not in item for item in result["playbooks"])
    assert result["limitations"]


async def test_list_filters_by_domain_provider_and_phase(tool: FinOpsPlaybooksTool) -> None:
    result = await tool.execute(
        {
            "action": "list",
            "domain": "Optimize Usage & Cost",
            "provider": "AWS",
            "phase": "optimize",
        }
    )
    assert result["returned_count"] >= 3
    for item in result["playbooks"]:
        assert item["domain"] == "Optimize Usage & Cost"
        assert "aws" in item["providers"]
        assert "optimize" in item["phases"]


async def test_list_filters_by_capability_case_insensitively(tool: FinOpsPlaybooksTool) -> None:
    result = await tool.execute({"action": "list", "capability": "anomaly management"})
    assert [item["id"] for item in result["playbooks"]] == ["anomaly-management"]


async def test_search_finds_commitment_playbook(tool: FinOpsPlaybooksTool) -> None:
    result = await tool.execute({"action": "search", "query": "savings plans reservations"})
    assert result["playbooks"][0]["id"] == "commitment-based-discounts"
    assert result["playbooks"][0]["score"] > 0


async def test_search_respects_limit(tool: FinOpsPlaybooksTool) -> None:
    result = await tool.execute({"action": "search", "query": "cost", "limit": 2})
    assert result["returned_count"] <= 2


async def test_get_returns_full_body(tool: FinOpsPlaybooksTool) -> None:
    result = await tool.execute({"action": "get", "id": "cost-allocation-tagging"})
    playbook: dict[str, Any] = result["playbook"]
    assert playbook["id"] == "cost-allocation-tagging"
    assert "## Steps" in playbook["body"]
    assert "finops__cost_by_tag" in playbook["related_tools"]


@pytest.mark.parametrize(
    "arguments",
    [
        {"action": "delete"},
        {"action": "search"},
        {"action": "search", "query": "x"},
        {"action": "search", "query": "q" * 201},
        {"action": "search", "query": "cost", "limit": 0},
        {"action": "get"},
        {"action": "get", "id": "../../etc/passwd"},
        {"action": "get", "id": "does-not-exist"},
        {"action": "list", "domain": "Not a domain"},
        {"action": "list", "phase": "someday"},
    ],
)
async def test_invalid_requests_raise_controlled_error(
    tool: FinOpsPlaybooksTool, arguments: dict[str, Any]
) -> None:
    with pytest.raises(InvalidPlaybookRequestError):
        await tool.execute(arguments)


def test_factory_registers_playbooks_tool() -> None:
    server = MulticloudMCPServer(Settings())
    context = NativeToolContext(server.router, server.health_monitor, server.finops_service)
    registry = build_native_tool_registry(context, ["playbooks"])
    assert registry.get("finops__playbooks").name == "finops__playbooks"


def test_playbooks_tool_enabled_by_default() -> None:
    assert "finops__playbooks" in _native_tool_names()
