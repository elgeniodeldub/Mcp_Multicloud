"""AWS Cost Explorer adapter for live FinOps queries."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Any

import boto3

from multicloud_mcp.finops.enums import CostMetric, FinOpsDimension
from multicloud_mcp.finops.exceptions import FinOpsQueryError
from multicloud_mcp.finops.models import FinOpsCostResult, FinOpsQuery


class AWSFinOpsProvider:
    """Query AWS Cost Explorer without exposing boto3 to MCP tools."""

    name = "aws"

    def __init__(
        self,
        client_factory: Callable[[], Any] | None = None,
        region_name: str | None = None,
    ) -> None:
        self._client_factory = client_factory or (
            lambda: boto3.client("ce", region_name=region_name)
        )

    async def query_cost(self, query: FinOpsQuery) -> list[FinOpsCostResult]:
        """Run GetCostAndUsage with provider-side grouping."""
        return await asyncio.to_thread(self._query_sync, query)

    def _query_sync(self, query: FinOpsQuery) -> list[FinOpsCostResult]:
        client = self._client_factory()
        group_by = self._group_by(query.group_by)
        metric_name = self._metric_name(query.metric)
        try:
            response = client.get_cost_and_usage(
                TimePeriod={
                    "Start": query.start_date.isoformat(),
                    "End": query.end_date.isoformat(),
                },
                Granularity="DAILY",
                Metrics=[metric_name],
                **({"GroupBy": group_by} if group_by else {}),
            )
        except Exception as exc:
            fallback = self._fallback_metric(query.metric, metric_name)
            if fallback is None:
                raise FinOpsQueryError(
                    f"AWS Cost Explorer query failed: {type(exc).__name__}"
                ) from exc
            try:
                response = client.get_cost_and_usage(
                    TimePeriod={
                        "Start": query.start_date.isoformat(),
                        "End": query.end_date.isoformat(),
                    },
                    Granularity="DAILY",
                    Metrics=[fallback],
                    **({"GroupBy": group_by} if group_by else {}),
                )
                metric_name = fallback
            except Exception as fallback_exc:
                raise FinOpsQueryError(
                    f"AWS Cost Explorer query failed: {type(fallback_exc).__name__}"
                ) from fallback_exc

        results: list[FinOpsCostResult] = []
        for period in response.get("ResultsByTime", []):
            period_start = self._date(period.get("TimePeriod", {}).get("Start"), query.start_date)
            period_end = self._date(period.get("TimePeriod", {}).get("End"), query.end_date)
            groups = period.get("Groups", [])
            if not groups and not group_by:
                groups = [
                    {
                        "Keys": [],
                        "Metrics": {
                            metric_name: period.get("Total", {}).get(
                                metric_name, {"Amount": "0", "Unit": "USD"}
                            )
                        },
                    }
                ]
            if not groups:
                groups = [{"Keys": [], "Metrics": {metric_name: {"Amount": "0", "Unit": "USD"}}}]
            for group in groups:
                metric = group.get("Metrics", {}).get(metric_name, {})
                amount = Decimal(str(metric.get("Amount", "0")))
                unit = str(metric.get("Unit", "USD"))
                values = self._values(query.group_by, group.get("Keys", []))
                results.append(
                    FinOpsCostResult(
                        provider_name=self.name,
                        sub_account_id=values.get(FinOpsDimension.ACCOUNT),
                        service_name=values.get(FinOpsDimension.SERVICE),
                        service_category=values.get(FinOpsDimension.SERVICE_CATEGORY),
                        region_id=values.get(FinOpsDimension.REGION),
                        billed_cost=amount if query.metric is CostMetric.BILLED else None,
                        effective_cost=amount,
                        currency=unit,
                        start_date=period_start,
                        end_date=period_end,
                    )
                )
        return results[: query.limit] if query.limit else results

    @staticmethod
    def _metric_name(metric: CostMetric) -> str:
        return "NetUnblendedCost" if metric is CostMetric.BILLED else "NetAmortizedCost"

    @staticmethod
    def _fallback_metric(metric: CostMetric, selected: str) -> str | None:
        if metric is CostMetric.BILLED and selected == "NetUnblendedCost":
            return "UnblendedCost"
        if metric is CostMetric.EFFECTIVE and selected == "NetAmortizedCost":
            return "AmortizedCost"
        return None

    @staticmethod
    def _group_by(dimensions: list[FinOpsDimension]) -> list[dict[str, str]]:
        mapping = {
            FinOpsDimension.ACCOUNT: "LINKED_ACCOUNT",
            FinOpsDimension.SERVICE: "SERVICE",
            FinOpsDimension.REGION: "REGION",
        }
        return [
            {"Type": "DIMENSION", "Key": mapping[dimension]}
            for dimension in dimensions
            if dimension in mapping
        ][:2]

    @staticmethod
    def _values(dimensions: list[FinOpsDimension], keys: list[Any]) -> dict[FinOpsDimension, str]:
        mapping = {
            FinOpsDimension.ACCOUNT: "LINKED_ACCOUNT",
            FinOpsDimension.SERVICE: "SERVICE",
            FinOpsDimension.REGION: "REGION",
        }
        provider_dimensions = [dimension for dimension in dimensions if dimension in mapping][:2]
        return {
            dimension: str(keys[index]) if index < len(keys) else "Unknown"
            for index, dimension in enumerate(provider_dimensions)
        }

    @staticmethod
    def _date(value: Any, fallback: date) -> date:
        return date.fromisoformat(value) if isinstance(value, str) else fallback
