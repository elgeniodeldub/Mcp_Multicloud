"""Google Cloud public list-price adapter.

This adapter only reads the Cloud Billing Catalog API. It does not query actual
usage, Cloud Billing exports, BigQuery, discounts, or amortized costs.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import httpx

from multicloud_mcp.finops.exceptions import FinOpsQueryError


class GCPListPriceProvider:
    """Query public GCP SKU prices from the Cloud Billing Catalog API."""

    name = "gcp"
    endpoint = "https://cloudbilling.googleapis.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("GCP_BILLING_API_KEY", "")
        self._client_factory = client_factory or httpx.AsyncClient

    async def list_prices(
        self,
        service_id: str,
        region: str | None = None,
        currency: str = "USD",
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """Return public SKU pricing for a GCP service."""
        if not self._api_key:
            raise FinOpsQueryError(
                "GCP_BILLING_API_KEY is required for GCP public list prices"
            )
        parent = service_id if service_id.startswith("services/") else f"services/{service_id}"
        params: dict[str, str | int] = {
            "key": self._api_key,
            "currencyCode": currency,
            "pageSize": min(max(page_size, 1), 5000),
        }
        if region:
            params["filter"] = f"serviceRegions:({region})"
        url = f"{self.endpoint}/{parent}/skus"
        try:
            async with self._client_factory(timeout=60) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise FinOpsQueryError(
                f"GCP Cloud Billing Catalog query failed: {type(exc).__name__}"
            ) from exc
        return [self._normalize_sku(sku) for sku in payload.get("skus", [])]

    @staticmethod
    def _normalize_sku(sku: dict[str, Any]) -> dict[str, Any]:
        pricing: list[dict[str, Any]] = []
        for item in sku.get("pricingInfo", []):
            expression = item.get("pricingExpression", {})
            rates = []
            for tier in expression.get("tieredRates", []):
                units = tier.get("unitPrice", {}).get("units", "0")
                nanos = tier.get("unitPrice", {}).get("nanos", 0)
                rates.append(
                    {
                        "start_usage_amount": str(tier.get("startUsageAmount", 0)),
                        "unit_price": str(
                            Decimal(str(units)) + Decimal(str(nanos)) / Decimal("1000000000")
                        ),
                    }
                )
            pricing.append(
                {
                    "effective_time": item.get("effectiveTime"),
                    "unit": expression.get("usageUnit"),
                    "unit_description": expression.get("usageUnitDescription"),
                    "rates": rates,
                }
            )
        return {
            "sku_id": sku.get("skuId"),
            "service_id": sku.get("serviceId"),
            "description": sku.get("description"),
            "category": sku.get("category"),
            "service_regions": sku.get("serviceRegions", []),
            "pricing": pricing,
        }
