"""MCP tool for native GCP public list-price lookup."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.finops.providers.gcp import GCPListPriceProvider
from multicloud_mcp.providers.base import ToolInfo


class GCPListPricesTool:
    """Expose public GCP SKU prices without querying actual spend."""

    def __init__(self, provider: GCPListPriceProvider | None = None) -> None:
        self.provider = provider or GCPListPriceProvider()

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="finops__gcp_list_prices",
            description=(
                "Get public GCP on-demand SKU prices from Cloud Billing Catalog. "
                "This is list pricing only, not actual cost."
            ),
            input_schema={
                "type": "object",
                "required": ["service_id"],
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Cloud Billing Catalog service ID or services/{id}.",
                    },
                    "region": {"type": "string"},
                    "currency": {"type": "string", "default": "USD"},
                    "page_size": {"type": "integer", "minimum": 1, "maximum": 5000},
                },
            },
            original_name="finops__gcp_list_prices",
            provider="finops",
            namespace="finops",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        service_id = str(arguments.get("service_id", "")).strip()
        if not service_id:
            return {"error": "service_id is required"}
        currency = str(arguments.get("currency", "USD")).upper()
        prices = await self.provider.list_prices(
            service_id,
            region=str(arguments["region"]) if arguments.get("region") else None,
            currency=currency,
            page_size=int(arguments.get("page_size", 100)),
        )
        return {
            "provider": "gcp",
            "pricing_model": "list_price",
            "currency": currency,
            "service_id": service_id,
            "prices": prices,
            "limitations": [
                "Public on-demand/list pricing only.",
                "Excludes discounts, credits, commitments, taxes, and actual usage cost.",
                "This tool does not use BigQuery or Cloud Billing exports.",
            ],
        }
