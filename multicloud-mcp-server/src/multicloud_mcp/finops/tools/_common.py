"""Shared response helpers for FinOps MCP tools."""

from decimal import Decimal
from typing import Any

from multicloud_mcp.finops.models import FinOpsCostResult
from multicloud_mcp.finops.services.cost_service import CostQueryResponse


def money(value: Decimal) -> str:
    """Serialize money deterministically without binary floating point."""
    return format(value, "f")


def response_metadata(response: CostQueryResponse) -> dict[str, Any]:
    return {
        "partial": response.partial,
        "providers_failed": response.providers_failed,
        "cache_hit": response.cache_hit,
        "duration_ms": round(response.duration_ms, 2),
    }


def result_dimension(result: FinOpsCostResult, dimension: str) -> str:
    values = {
        "provider": result.provider_name,
        "account": result.sub_account_id or "Unknown",
        "service": result.service_name or "Unknown",
        "service_category": result.service_category or "Other",
        "region": result.region_id or "Unknown",
    }
    return values[dimension]
