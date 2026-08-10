"""Canonical models shared by multicloud application services."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CloudProvider(StrEnum):
    AWS = "aws"
    AZURE = "azure"
    OTHER = "other"


class ResourceState(StrEnum):
    UNKNOWN = "unknown"
    RUNNING = "running"
    STOPPED = "stopped"
    ACTIVE = "active"
    DELETED = "deleted"
    FAILED = "failed"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DomainModel(BaseModel):
    model_config = ConfigDict()


class CloudResource(DomainModel):
    id: str
    provider: CloudProvider
    name: str | None = None
    resource_type: str
    account_id: str | None = None
    region: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    state: ResourceState = ResourceState.UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComputeResource(CloudResource):
    resource_type: str = "compute"
    sku: str | None = None
    cpu: Decimal | None = None
    memory_gib: Decimal | None = None


class StorageResource(CloudResource):
    resource_type: str = "storage"
    capacity_gib: Decimal | None = None
    storage_class: str | None = None


class CostRecord(DomainModel):
    provider: CloudProvider
    amount: Decimal
    currency: str
    period_start: date
    period_end: date
    service: str | None = None
    region: str | None = None
    account_id: str | None = None


class CostReport(DomainModel):
    records: list[CostRecord] = Field(default_factory=list)
    totals_by_currency: dict[str, Decimal] = Field(default_factory=dict)

    @classmethod
    def from_records(cls, records: list[CostRecord]) -> CostReport:
        totals: dict[str, Decimal] = {}
        for record in records:
            totals[record.currency] = totals.get(record.currency, Decimal("0")) + record.amount
        return cls(records=records, totals_by_currency=totals)


class SecurityFinding(DomainModel):
    provider: CloudProvider
    resource: CloudResource | None = None
    severity: Severity
    control_id: str
    title: str
    description: str
