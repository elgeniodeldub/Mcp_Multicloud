"""Small provider-to-domain normalization helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from multicloud_mcp.domain.models import (
    CloudProvider,
    CloudResource,
    CostRecord,
    ResourceState,
    Severity,
)


def normalize_provider(value: str) -> CloudProvider:
    try:
        return CloudProvider(value.lower())
    except ValueError:
        return CloudProvider.OTHER


def normalize_state(value: Any) -> ResourceState:
    text = str(value or "").lower()
    if text in {"running", "started", "available", "online"}:
        return ResourceState.RUNNING
    if text in {"stopped", "deallocated", "offline"}:
        return ResourceState.STOPPED
    if text in {"active", "succeeded", "ready"}:
        return ResourceState.ACTIVE
    if text in {"deleted", "terminated"}:
        return ResourceState.DELETED
    if text in {"failed", "error"}:
        return ResourceState.FAILED
    return ResourceState.UNKNOWN


def normalize_severity(value: Any) -> Severity:
    text = str(value or "").lower()
    try:
        return Severity(text)
    except ValueError:
        return Severity.UNKNOWN


def normalize_tags(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def resource_from_mapping(provider: str, data: dict[str, Any]) -> CloudResource:
    return CloudResource(
        id=str(data.get("id") or data.get("resourceId") or data.get("arn") or "unknown"),
        provider=normalize_provider(provider),
        name=data.get("name") or data.get("resourceName"),
        resource_type=str(data.get("resource_type") or data.get("type") or "unknown"),
        account_id=data.get("account_id") or data.get("subscriptionId"),
        region=data.get("region") or data.get("location") or data.get("resourceLocation"),
        tags=normalize_tags(data.get("tags")),
        state=normalize_state(data.get("state") or data.get("status")),
        metadata=data,
    )


def cost_record_from_finops(result: Any) -> CostRecord:
    return CostRecord(
        provider=normalize_provider(str(result.provider_name)),
        amount=Decimal(str(result.effective_cost)),
        currency=result.currency,
        period_start=result.start_date,
        period_end=result.end_date,
        service=result.service_name,
        region=result.region_id,
        account_id=result.sub_account_id,
    )
