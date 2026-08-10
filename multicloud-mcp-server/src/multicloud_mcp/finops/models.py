"""Normalized FinOps domain models.

This is a small FOCUS-aligned domain model for live API queries. It is not a
FOCUS compliance claim or a persistent FOCUS dataset implementation.
"""

from datetime import date, timedelta
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from multicloud_mcp.finops.enums import CostMetric, FinOpsDimension


class FinOpsCostResult(BaseModel):
    """One normalized cost row returned by a live provider query."""

    provider_name: str
    sub_account_id: str | None = None
    service_name: str | None = None
    service_category: str | None = None
    region_id: str | None = None
    billed_cost: Decimal | None = None
    effective_cost: Decimal
    currency: str
    start_date: date
    end_date: date


class FinOpsQuery(BaseModel):
    """Provider-independent live cost query."""

    start_date: date
    end_date: date
    metric: CostMetric = CostMetric.EFFECTIVE
    group_by: list[FinOpsDimension] = Field(default_factory=list)
    providers: list[str] | None = None
    limit: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_period(self) -> "FinOpsQuery":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be later than start_date")
        return self

    @property
    def cache_key(self) -> str:
        """Return a stable key that separates all query scopes."""
        providers = ",".join(sorted(self.providers or ["aws", "azure"]))
        dimensions = ",".join(sorted(d.value for d in self.group_by))
        return (
            f"finops:{providers}:{self.start_date.isoformat()}:{self.end_date.isoformat()}"
            f":{self.metric.value}:{dimensions}:{self.limit or ''}"
        )


def period_dates(period: str, today: date | None = None) -> tuple[date, date]:
    """Resolve a small set of common inclusive/exclusive date periods."""
    current = today or date.today()
    normalized = period.lower()
    if normalized == "month_to_date":
        return current.replace(day=1), current + timedelta(days=1)
    if normalized == "last_7_days":
        return current - timedelta(days=6), current + timedelta(days=1)
    if normalized == "last_30_days":
        return current - timedelta(days=29), current + timedelta(days=1)
    if normalized == "previous_month":
        first = current.replace(day=1)
        previous_end = first
        previous_start = (first - timedelta(days=1)).replace(day=1)
        return previous_start, previous_end
    if normalized == "current_month":
        return current.replace(day=1), current + timedelta(days=1)
    raise ValueError(f"Unsupported period: {period}")
