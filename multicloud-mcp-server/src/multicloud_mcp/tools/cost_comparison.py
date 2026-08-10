"""Multicloud cost comparison tool."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class CostComparisonTool:
    """Compare costs between AWS and Azure for equivalent services."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__compare_cost",
            description=(
                "Compare estimated costs between AWS and Azure for equivalent services. "
                "Supports compute, storage, database, and networking services."
            ),
            input_schema={
                "type": "object",
                "required": ["service_type", "region_aws", "region_azure", "specs"],
                "properties": {
                    "service_type": {
                        "type": "string",
                        "enum": ["compute", "storage", "database", "networking", "kubernetes"],
                        "description": "Type of cloud service to compare",
                    },
                    "region_aws": {
                        "type": "string",
                        "description": "AWS region (e.g., us-east-1)",
                    },
                    "region_azure": {
                        "type": "string",
                        "description": "Azure region (e.g., eastus)",
                    },
                    "specs": {
                        "type": "object",
                        "description": "Service specifications",
                        "properties": {
                            "vcpu": {"type": "integer"},
                            "memory_gb": {"type": "integer"},
                            "storage_gb": {"type": "integer"},
                            "storage_type": {
                                "type": "string",
                                "enum": ["ssd", "hdd", "nvme"],
                            },
                        },
                    },
                },
            },
            original_name="multicloud__compare_cost",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute cost comparison."""
        service_type = arguments.get("service_type", "compute")
        region_aws = arguments.get("region_aws", "us-east-1")
        region_azure = arguments.get("region_azure", "eastus")
        specs = arguments.get("specs", {})

        comparisons = {
            "compute": self._compare_compute(specs, region_aws, region_azure),
            "storage": self._compare_storage(specs, region_aws, region_azure),
            "database": self._compare_database(specs, region_aws, region_azure),
        }

        return {
            "service_type": service_type,
            "regions": {"aws": region_aws, "azure": region_azure},
            "comparison": comparisons.get(service_type, {}),
            "recommendation": self._get_recommendation(comparisons.get(service_type, {})),
        }

    def _compare_compute(self, specs: dict, aws_region: str, azure_region: str) -> dict:
        vcpu = specs.get("vcpu", 4)
        memory = specs.get("memory_gb", 16)
        aws_price = round((vcpu * 0.048) + (memory * 0.012), 4)
        azure_price = round((vcpu * 0.052) + (memory * 0.014), 4)
        return {
            "aws": {
                "instance_family": "m6i" if vcpu <= 8 else "m6g",
                "price_per_hour": aws_price,
                "price_per_month": round(aws_price * 730, 2),
            },
            "azure": {
                "instance_family": "Dsv5" if vcpu <= 8 else "Ddsv5",
                "price_per_hour": azure_price,
                "price_per_month": round(azure_price * 730, 2),
            },
            "savings": {
                "winner": "aws" if aws_price < azure_price else "azure",
                "percentage": round(abs(aws_price - azure_price) / max(aws_price, azure_price) * 100, 1),
            },
        }

    def _compare_storage(self, specs: dict, aws_region: str, azure_region: str) -> dict:
        storage_gb = specs.get("storage_gb", 1000)
        storage_type = specs.get("storage_type", "ssd")
        pricing = {
            "ssd": {"aws": 0.10, "azure": 0.12},
            "hdd": {"aws": 0.045, "azure": 0.048},
            "nvme": {"aws": 0.125, "azure": 0.137},
        }
        aws_price = pricing.get(storage_type, pricing["ssd"])["aws"]
        azure_price = pricing.get(storage_type, pricing["ssd"])["azure"]
        return {
            "aws": {
                "service": "EBS gp3" if storage_type == "ssd" else "EBS st1",
                "price_per_gb_month": aws_price,
                "total_monthly": round(aws_price * storage_gb, 2),
            },
            "azure": {
                "service": "Managed Disks Premium SSD" if storage_type == "ssd" else "Standard HDD",
                "price_per_gb_month": azure_price,
                "total_monthly": round(azure_price * storage_gb, 2),
            },
        }

    def _compare_database(self, specs: dict, aws_region: str, azure_region: str) -> dict:
        return {
            "aws": {"service": "RDS PostgreSQL", "price_per_hour": 0.35},
            "azure": {"service": "Azure Database for PostgreSQL", "price_per_hour": 0.38},
        }

    def _get_recommendation(self, comparison: dict) -> str:
        if "savings" in comparison:
            winner = comparison["savings"]["winner"]
            pct = comparison["savings"]["percentage"]
            return f"{winner.upper()} is approximately {pct}% more cost-effective for this workload."
        return "Compare specific services for detailed recommendations."
