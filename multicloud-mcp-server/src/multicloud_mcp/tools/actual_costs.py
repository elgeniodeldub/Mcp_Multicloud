"""Actual, non-amortized cloud cost queries."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from typing import Any

import boto3
import httpx
from azure.identity import DefaultAzureCredential

from multicloud_mcp.providers.base import ToolInfo


class ActualCostsTool:
    """Read actual non-amortized costs from AWS and Azure billing APIs."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="finops__get_actual_costs",
            description=(
                "Read-only historical actual/non-amortized spend from AWS Cost Explorer "
                "and Azure Cost Management. Use this for billed AWS/Azure spend, not list "
                "price estimates; GCP actual spend is not supported. Returns grouped cost "
                "data by provider/period and never performs cloud mutations. AWS uses "
                "UnblendedCost and Azure uses PreTaxCost. "
                "Results are reported per provider and are not price-list estimates."
            ),
            input_schema={
                "type": "object",
                "required": ["start_date", "end_date"],
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Inclusive UTC date, YYYY-MM-DD.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Exclusive UTC date, YYYY-MM-DD.",
                    },
                    "granularity": {
                        "type": "string",
                        "enum": ["DAILY", "MONTHLY"],
                        "default": "DAILY",
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["SERVICE", "REGION", "LINKED_ACCOUNT"],
                        "default": "SERVICE",
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                },
            },
            original_name="finops__get_actual_costs",
            provider="finops",
            namespace="finops",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        start = self._parse_date(arguments.get("start_date"))
        end = self._parse_date(arguments.get("end_date"))
        if end <= start:
            raise ValueError("end_date must be later than start_date")

        granularity = arguments.get("granularity", "DAILY").upper()
        group_by = arguments.get("group_by", "SERVICE").upper()
        providers = arguments.get("providers") or ["aws", "azure"]
        tasks = []
        if "aws" in providers:
            tasks.append(self._aws_costs(start, end, granularity, group_by))
        if "azure" in providers:
            tasks.append(self._azure_costs(start, end, granularity, group_by))
        results = await asyncio.gather(*tasks)

        return {
            "cost_basis": "actual_non_amortized",
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "granularity": granularity,
            "group_by": group_by,
            "providers": {item["provider"]: item for item in results},
            "limitations": [
                "AWS uses UnblendedCost; Azure uses PreTaxCost.",
                "Provider billing data can have a reporting delay.",
                "Values are not directly comparable across currencies or provider billing models.",
            ],
        }

    async def _aws_costs(
        self, start: date, end: date, granularity: str, group_by: str
    ) -> dict[str, Any]:
        def query() -> dict[str, Any]:
            client = boto3.client("ce")
            response = client.get_cost_and_usage(
                TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
                Granularity=granularity,
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": group_by}],
            )
            periods = []
            total = 0.0
            currency = "USD"
            for period in response.get("ResultsByTime", []):
                groups = []
                period_total = 0.0
                for group in period.get("Groups", []):
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    currency = group["Metrics"]["UnblendedCost"].get("Unit", currency)
                    period_total += amount
                    groups.append({"key": group.get("Keys", ["Unknown"])[0], "amount": amount})
                total += period_total
                periods.append(
                    {
                        "start": period["TimePeriod"]["Start"],
                        "end": period["TimePeriod"]["End"],
                        "total": period_total,
                        "groups": groups,
                    }
                )
            return {"provider": "aws", "currency": currency, "total": total, "periods": periods}

        return await asyncio.to_thread(query)

    async def _azure_costs(
        self, start: date, end: date, granularity: str, group_by: str
    ) -> dict[str, Any]:
        subscription_id = self._required_env("AZURE_SUBSCRIPTION_ID")
        credential = DefaultAzureCredential()
        token = await asyncio.to_thread(
            credential.get_token, "https://management.azure.com/.default"
        )
        scope = f"/subscriptions/{subscription_id}"
        url = f"https://management.azure.com{scope}/providers/Microsoft.CostManagement/query"
        grouping = {
            "SERVICE": "ServiceName",
            "REGION": "ResourceLocation",
            "LINKED_ACCOUNT": "SubscriptionName",
        }[group_by]
        body = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": self._utc(start), "to": self._utc(end)},
            "dataset": {
                "granularity": "Daily" if granularity == "DAILY" else "Monthly",
                "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": grouping}],
            },
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                params={"api-version": "2025-03-01"},
                headers={"Authorization": f"Bearer {token.token}"},
                json=body,
            )
            response.raise_for_status()
            payload = response.json()

        columns = [column["name"] for column in payload.get("properties", {}).get("columns", [])]
        rows = payload.get("properties", {}).get("rows", [])
        total_index = columns.index("PreTaxCost") if "PreTaxCost" in columns else 0
        currency_index = columns.index("Currency") if "Currency" in columns else None
        group_index = columns.index(grouping) if grouping in columns else None
        total = sum(float(row[total_index] or 0) for row in rows)
        groups: dict[str, float] = {}
        for row in rows:
            key = str(row[group_index]) if group_index is not None else "Total"
            groups[key] = groups.get(key, 0.0) + float(row[total_index] or 0)
        currency = str(rows[0][currency_index]) if rows and currency_index is not None else "USD"
        return {
            "provider": "azure",
            "currency": currency,
            "total": total,
            "periods": [
                {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "total": total,
                    "groups": [{"key": key, "amount": amount} for key, amount in groups.items()],
                }
            ],
        }

    @staticmethod
    def _parse_date(value: Any) -> date:
        if not isinstance(value, str):
            raise ValueError("start_date and end_date must use YYYY-MM-DD")
        return date.fromisoformat(value)

    @staticmethod
    def _utc(value: date) -> str:
        return (
            datetime(value.year, value.month, value.day, tzinfo=UTC)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _required_env(name: str) -> str:
        import os

        value = os.environ.get(name)
        if not value:
            raise ValueError(f"{name} is required for Azure Cost Management")
        return value
