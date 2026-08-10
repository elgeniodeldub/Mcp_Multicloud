"""FinOps list-price comparison tool.

This tool deliberately compares public on-demand/list prices. It does not
represent invoiced, discounted, amortized, or allocated cloud spend.
"""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class ListPriceComparisonTool:
    """Compare illustrative AWS and Azure on-demand list prices."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="finops__compare_list_prices",
            description=(
                "Compare AWS and Azure public on-demand list prices for equivalent "
                "workload shapes. Results are estimates and exclude discounts, "
                "credits, reservations, amortization, taxes, and invoiced spend."
            ),
            input_schema={
                "type": "object",
                "required": ["service_type", "region_aws", "region_azure", "specs"],
                "properties": {
                    "service_type": {
                        "type": "string",
                        "enum": ["compute", "storage", "database"],
                    },
                    "region_aws": {"type": "string"},
                    "region_azure": {"type": "string"},
                    "specs": {
                        "type": "object",
                        "description": "Workload shape used for the list-price estimate.",
                        "properties": {
                            "vcpu": {"type": "integer", "minimum": 1},
                            "memory_gb": {"type": "number", "minimum": 1},
                            "storage_gb": {"type": "number", "minimum": 1},
                            "storage_type": {"type": "string", "enum": ["ssd", "hdd"]},
                        },
                    },
                },
            },
            original_name="finops__compare_list_prices",
            provider="finops",
            namespace="finops",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        service_type = arguments.get("service_type", "compute")
        region_aws = arguments.get("region_aws", "us-east-1")
        region_azure = arguments.get("region_azure", "eastus")
        specs = arguments.get("specs", {})

        comparisons = {
            "compute": self._compare_compute(specs),
            "storage": self._compare_storage(specs),
            "database": self._compare_database(),
        }
        comparison = comparisons.get(service_type, {})
        return {
            "pricing_model": "list_price",
            "estimate_type": "public_on_demand",
            "regions": {"aws": region_aws, "azure": region_azure},
            "service_type": service_type,
            "comparison": comparison,
            "recommendation": self._get_recommendation(comparison),
            "limitations": [
                "Excludes discounts, credits, reservations, commitments, taxes, and amortization.",
                "Use provider pricing catalogs to refresh the illustrative rates before production use.",
            ],
        }

    def _compare_compute(self, specs: dict[str, Any]) -> dict[str, Any]:
        vcpu = specs.get("vcpu", 4)
        memory = specs.get("memory_gb", 16)
        aws_price = round((vcpu * 0.048) + (memory * 0.012), 4)
        azure_price = round((vcpu * 0.052) + (memory * 0.014), 4)
        return {
            "aws": {"instance_family": "m6i" if vcpu <= 8 else "m6g", "price_per_hour": aws_price,
                    "price_per_month": round(aws_price * 730, 2)},
            "azure": {"instance_family": "Dsv5" if vcpu <= 8 else "Ddsv5", "price_per_hour": azure_price,
                      "price_per_month": round(azure_price * 730, 2)},
            "difference": {"winner": "aws" if aws_price < azure_price else "azure",
                           "percentage": round(abs(aws_price - azure_price) / max(aws_price, azure_price) * 100, 1)},
        }

    def _compare_storage(self, specs: dict[str, Any]) -> dict[str, Any]:
        storage_gb = specs.get("storage_gb", 1000)
        storage_type = specs.get("storage_type", "ssd")
        pricing = {"ssd": {"aws": 0.10, "azure": 0.12}, "hdd": {"aws": 0.045, "azure": 0.048}}
        rates = pricing.get(storage_type, pricing["ssd"])
        return {
            "aws": {"service": "EBS gp3" if storage_type == "ssd" else "EBS st1",
                    "price_per_gb_month": rates["aws"], "total_monthly": round(rates["aws"] * storage_gb, 2)},
            "azure": {"service": "Managed Disks Premium SSD" if storage_type == "ssd" else "Standard HDD",
                      "price_per_gb_month": rates["azure"], "total_monthly": round(rates["azure"] * storage_gb, 2)},
        }

    def _compare_database(self) -> dict[str, Any]:
        return {"aws": {"service": "RDS PostgreSQL", "price_per_hour": 0.35},
                "azure": {"service": "Azure Database for PostgreSQL", "price_per_hour": 0.38}}

    def _get_recommendation(self, comparison: dict[str, Any]) -> str:
        difference = comparison.get("difference")
        if difference:
            return (f"{difference['winner'].upper()} has the lower public list-price estimate "
                    f"by approximately {difference['percentage']}%.")
        return "Compare the public list-price estimates for the selected workload shape."


# Backwards-compatible import for consumers of the original module/class.
CostComparisonTool = ListPriceComparisonTool
