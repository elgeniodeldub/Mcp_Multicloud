"""FinOps query enums."""

from enum import StrEnum


class CostMetric(StrEnum):
    """Cost measure requested from the provider."""

    BILLED = "billed_cost"
    EFFECTIVE = "effective_cost"


class FinOpsDimension(StrEnum):
    """Normalized dimensions supported by the live query layer."""

    PROVIDER = "provider"
    ACCOUNT = "account"
    SERVICE = "service"
    SERVICE_CATEGORY = "service_category"
    REGION = "region"
