"""Azure Cost Management Query API adapter for live FinOps queries."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import httpx
from azure.identity import DefaultAzureCredential

from multicloud_mcp.finops.enums import CostMetric, FinOpsDimension
from multicloud_mcp.finops.exceptions import FinOpsQueryError
from multicloud_mcp.finops.models import FinOpsCostResult, FinOpsQuery


class AzureFinOpsProvider:
    """Query Azure Cost Management while keeping credentials inside the adapter."""

    name = "azure"

    def __init__(
        self,
        subscription_id: str | None = None,
        credential: Any | None = None,
        client_factory: Callable[..., Any] | None = None,
        api_version: str = "2025-03-01",
    ) -> None:
        self.subscription_id = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID", "")
        self._credential = credential
        self._client_factory = client_factory or httpx.AsyncClient
        self.api_version = api_version

    async def query_cost(self, query: FinOpsQuery) -> list[FinOpsCostResult]:
        """Run one grouped Cost Management query at subscription scope."""
        if not self.subscription_id:
            raise FinOpsQueryError("AZURE_SUBSCRIPTION_ID is required for Azure Cost Management")
        credential = self._credential or DefaultAzureCredential()
        try:
            token = await asyncio.to_thread(
                credential.get_token, "https://management.azure.com/.default"
            )
            body = self._request_body(query)
            url = (
                f"https://management.azure.com/subscriptions/{self.subscription_id}"
                "/providers/Microsoft.CostManagement/query"
            )
            async with self._client_factory(timeout=60) as client:
                response = await client.post(
                    url,
                    params={"api-version": self.api_version},
                    headers={"Authorization": f"Bearer {token.token}"},
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()
        except FinOpsQueryError:
            raise
        except Exception as exc:
            raise FinOpsQueryError(
                f"Azure Cost Management query failed: {type(exc).__name__}"
            ) from exc
        return self._parse_response(payload, query)

    def _request_body(self, query: FinOpsQuery) -> dict[str, Any]:
        grouping = [
            {"type": "Dimension", "name": self._dimension_name(dimension)}
            for dimension in query.group_by
            if dimension
            in {FinOpsDimension.ACCOUNT, FinOpsDimension.SERVICE, FinOpsDimension.REGION}
        ]
        return {
            "type": "ActualCost" if query.metric is CostMetric.BILLED else "AmortizedCost",
            "timeframe": "Custom",
            "timePeriod": {"from": self._utc(query.start_date), "to": self._utc(query.end_date)},
            "dataset": {
                "granularity": "Daily",
                "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                **({"grouping": grouping} if grouping else {}),
            },
        }

    @staticmethod
    def _dimension_name(dimension: FinOpsDimension) -> str:
        return {
            FinOpsDimension.ACCOUNT: "SubscriptionId",
            FinOpsDimension.SERVICE: "ServiceName",
            FinOpsDimension.REGION: "ResourceLocation",
        }[dimension]

    def _parse_response(
        self, payload: dict[str, Any], query: FinOpsQuery
    ) -> list[FinOpsCostResult]:
        properties = payload.get("properties", {})
        columns = [str(column.get("name")) for column in properties.get("columns", [])]
        rows = properties.get("rows", [])
        try:
            cost_index = columns.index("PreTaxCost")
        except ValueError as exc:
            raise FinOpsQueryError(
                "Azure Cost Management response has no PreTaxCost column"
            ) from exc
        currency_index = columns.index("Currency") if "Currency" in columns else None
        dimensions = [
            dimension
            for dimension in query.group_by
            if dimension
            in {FinOpsDimension.ACCOUNT, FinOpsDimension.SERVICE, FinOpsDimension.REGION}
        ]
        results: list[FinOpsCostResult] = []
        for row in rows:
            values: dict[FinOpsDimension, str] = {
                dimension: self._row_value(row, columns, self._dimension_name(dimension))
                for dimension in dimensions
            }
            amount = Decimal(str(row[cost_index] or "0"))
            currency = str(row[currency_index]) if currency_index is not None else "USD"
            results.append(
                FinOpsCostResult(
                    provider_name=self.name,
                    sub_account_id=values.get(FinOpsDimension.ACCOUNT),
                    service_name=values.get(FinOpsDimension.SERVICE),
                    service_category=values.get(FinOpsDimension.SERVICE_CATEGORY),
                    region_id=values.get(FinOpsDimension.REGION),
                    billed_cost=amount if query.metric is CostMetric.BILLED else None,
                    effective_cost=amount,
                    currency=currency,
                    start_date=query.start_date,
                    end_date=query.end_date,
                )
            )
        if not results:
            results.append(
                FinOpsCostResult(
                    provider_name=self.name,
                    sub_account_id=self.subscription_id,
                    billed_cost=Decimal("0") if query.metric is CostMetric.BILLED else None,
                    effective_cost=Decimal("0"),
                    currency="USD",
                    start_date=query.start_date,
                    end_date=query.end_date,
                )
            )
        return results[: query.limit] if query.limit else results

    @staticmethod
    def _row_value(row: list[Any], columns: list[str], name: str) -> str:
        try:
            index = columns.index(name)
        except ValueError:
            return "Unknown"
        return str(row[index]) if index < len(row) and row[index] is not None else "Unknown"

    @staticmethod
    def _utc(value: date) -> str:
        return (
            datetime(value.year, value.month, value.day, tzinfo=UTC)
            .isoformat()
            .replace("+00:00", "Z")
        )
