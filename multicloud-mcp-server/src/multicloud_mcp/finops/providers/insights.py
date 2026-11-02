"""Forecast, anomaly, budget, and tag-cost adapters for AWS and Azure.

All calls are read-only. Provider SDK/HTTP clients are injectable so tests never
reach a real cloud API.
"""

from __future__ import annotations

import asyncio
import os
import statistics
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
import httpx
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel

from multicloud_mcp.finops.exceptions import FinOpsQueryError

AZURE_MANAGEMENT = "https://management.azure.com"


class ForecastResult(BaseModel):
    """Forecasted spend for one provider and period."""

    provider_name: str
    amount: Decimal
    currency: str
    start_date: date
    end_date: date
    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None


class CostAnomaly(BaseModel):
    """One cost anomaly, either provider-native or statistically detected."""

    provider_name: str
    source: str
    start_date: date
    end_date: date | None = None
    dimension: str | None = None
    impact: Decimal
    expected: Decimal | None = None
    actual: Decimal | None = None
    currency: str = "USD"
    score: float | None = None
    root_causes: list[dict[str, str]] = []


class BudgetStatus(BaseModel):
    """Budget limit versus actual and forecasted spend."""

    provider_name: str
    name: str
    limit: Decimal
    actual: Decimal
    forecast: Decimal | None = None
    currency: str
    time_grain: str | None = None

    @property
    def utilization(self) -> Decimal:
        return (self.actual / self.limit * 100) if self.limit else Decimal("0")


class TagCost(BaseModel):
    """Spend grouped by one value of a tag key."""

    provider_name: str
    tag_key: str
    tag_value: str
    amount: Decimal
    currency: str


def detect_anomalies(
    provider: str,
    daily: list[tuple[date, Decimal]],
    currency: str,
    threshold: float = 3.0,
    min_impact: Decimal = Decimal("1"),
) -> list[CostAnomaly]:
    """Flag days whose cost deviates from the trailing baseline by a robust z-score.

    Uses median and MAD so a single spike does not hide itself by inflating the
    baseline. Each day is compared only with the days before it.
    """
    anomalies: list[CostAnomaly] = []
    ordered = sorted(daily)
    for index in range(7, len(ordered)):
        day, value = ordered[index]
        window = [float(cost) for _, cost in ordered[max(0, index - 28) : index]]
        median = statistics.median(window)
        mad = statistics.median(abs(item - median) for item in window)
        spread = mad * 1.4826 or max(median * 0.1, 0.01)
        score = (float(value) - median) / spread
        impact = value - Decimal(str(round(median, 6)))
        if abs(score) >= threshold and abs(impact) >= min_impact:
            anomalies.append(
                CostAnomaly(
                    provider_name=provider,
                    source="statistical",
                    start_date=day,
                    end_date=day + timedelta(days=1),
                    impact=impact,
                    expected=Decimal(str(round(median, 6))),
                    actual=value,
                    currency=currency,
                    score=round(score, 2),
                )
            )
    return anomalies


class AWSInsightsProvider:
    """AWS Cost Explorer and Budgets read-only insights."""

    name = "aws"

    def __init__(
        self,
        ce_factory: Callable[[], Any] | None = None,
        budgets_factory: Callable[[], Any] | None = None,
        sts_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._ce = ce_factory or (lambda: boto3.client("ce"))
        self._budgets = budgets_factory or (lambda: boto3.client("budgets"))
        self._sts = sts_factory or (lambda: boto3.client("sts"))

    async def forecast(self, start: date, end: date) -> ForecastResult:
        return await asyncio.to_thread(self._forecast, start, end)

    def _forecast(self, start: date, end: date) -> ForecastResult:
        try:
            response = self._ce().get_cost_forecast(
                TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY",
                PredictionIntervalLevel=80,
            )
        except Exception as exc:
            raise FinOpsQueryError(f"AWS cost forecast failed: {type(exc).__name__}") from exc
        total = response.get("Total", {})
        lower = upper = Decimal("0")
        for item in response.get("ForecastResultsByTime", []):
            lower += Decimal(str(item.get("PredictionIntervalLowerBound", "0")))
            upper += Decimal(str(item.get("PredictionIntervalUpperBound", "0")))
        return ForecastResult(
            provider_name=self.name,
            amount=Decimal(str(total.get("Amount", "0"))),
            currency=str(total.get("Unit", "USD")),
            start_date=start,
            end_date=end,
            lower_bound=lower or None,
            upper_bound=upper or None,
        )

    async def anomalies(self, start: date, end: date) -> list[CostAnomaly]:
        return await asyncio.to_thread(self._anomalies, start, end)

    def _anomalies(self, start: date, end: date) -> list[CostAnomaly]:
        client = self._ce()
        anomalies: list[CostAnomaly] = []
        token: str | None = None
        try:
            while True:
                response = client.get_anomalies(
                    DateInterval={"StartDate": start.isoformat(), "EndDate": end.isoformat()},
                    MaxResults=100,
                    **({"NextPageToken": token} if token else {}),
                )
                for item in response.get("Anomalies", []):
                    impact = item.get("Impact", {})
                    anomalies.append(
                        CostAnomaly(
                            provider_name=self.name,
                            source="aws_cost_anomaly_detection",
                            start_date=date.fromisoformat(
                                str(item.get("AnomalyStartDate", start.isoformat()))[:10]
                            ),
                            end_date=(
                                date.fromisoformat(str(item["AnomalyEndDate"])[:10])
                                if item.get("AnomalyEndDate")
                                else None
                            ),
                            dimension=item.get("DimensionValue"),
                            impact=Decimal(str(impact.get("TotalImpact", "0"))),
                            expected=_optional_decimal(impact.get("TotalExpectedSpend")),
                            actual=_optional_decimal(impact.get("TotalActualSpend")),
                            score=_optional_float(item.get("AnomalyScore", {}).get("MaxScore")),
                            root_causes=[
                                {key: str(value) for key, value in cause.items()}
                                for cause in item.get("RootCauses", [])
                            ],
                        )
                    )
                token = response.get("NextPageToken")
                if not token:
                    return anomalies
        except Exception as exc:
            raise FinOpsQueryError(f"AWS anomaly query failed: {type(exc).__name__}") from exc

    async def budgets(self) -> list[BudgetStatus]:
        return await asyncio.to_thread(self._budgets_sync)

    def _budgets_sync(self) -> list[BudgetStatus]:
        try:
            account_id = self._sts().get_caller_identity()["Account"]
            client = self._budgets()
            budgets: list[BudgetStatus] = []
            token: str | None = None
            while True:
                response = client.describe_budgets(
                    AccountId=account_id, MaxResults=100, **({"NextToken": token} if token else {})
                )
                for item in response.get("Budgets", []):
                    limit = item.get("BudgetLimit", {})
                    spend = item.get("CalculatedSpend", {})
                    forecast = spend.get("ForecastedSpend")
                    budgets.append(
                        BudgetStatus(
                            provider_name=self.name,
                            name=str(item.get("BudgetName", "")),
                            limit=Decimal(str(limit.get("Amount", "0"))),
                            actual=Decimal(str(spend.get("ActualSpend", {}).get("Amount", "0"))),
                            forecast=Decimal(str(forecast["Amount"])) if forecast else None,
                            currency=str(limit.get("Unit", "USD")),
                            time_grain=item.get("TimeUnit"),
                        )
                    )
                token = response.get("NextToken")
                if not token:
                    return budgets
        except Exception as exc:
            raise FinOpsQueryError(f"AWS budgets query failed: {type(exc).__name__}") from exc

    async def cost_by_tag(self, tag_key: str, start: date, end: date) -> list[TagCost]:
        return await asyncio.to_thread(self._cost_by_tag, tag_key, start, end)

    def _cost_by_tag(self, tag_key: str, start: date, end: date) -> list[TagCost]:
        try:
            response = self._ce().get_cost_and_usage(
                TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "TAG", "Key": tag_key}],
            )
        except Exception as exc:
            raise FinOpsQueryError(f"AWS tag cost query failed: {type(exc).__name__}") from exc
        totals: dict[tuple[str, str], Decimal] = {}
        for period in response.get("ResultsByTime", []):
            for group in period.get("Groups", []):
                raw = str((group.get("Keys") or [""])[0])
                value = raw.split("$", 1)[1] if "$" in raw else raw
                metric = group.get("Metrics", {}).get("UnblendedCost", {})
                key = (value or "(untagged)", str(metric.get("Unit", "USD")))
                totals[key] = totals.get(key, Decimal("0")) + Decimal(
                    str(metric.get("Amount", "0"))
                )
        return [
            TagCost(
                provider_name=self.name,
                tag_key=tag_key,
                tag_value=value,
                amount=amount,
                currency=currency,
            )
            for (value, currency), amount in totals.items()
        ]


class AzureInsightsProvider:
    """Azure Cost Management and Consumption read-only insights."""

    name = "azure"

    def __init__(
        self,
        subscription_id: str | None = None,
        credential: Any | None = None,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.subscription_id = subscription_id or os.environ.get("AZURE_SUBSCRIPTION_ID", "")
        self._credential = credential
        self._client_factory = client_factory or httpx.AsyncClient

    @property
    def _scope(self) -> str:
        if not self.subscription_id:
            raise FinOpsQueryError("AZURE_SUBSCRIPTION_ID is required for Azure Cost Management")
        return f"/subscriptions/{self.subscription_id}"

    async def _request(
        self, method: str, path: str, api_version: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{AZURE_MANAGEMENT}{self._scope}{path}"
        credential = self._credential or DefaultAzureCredential()
        try:
            token = await asyncio.to_thread(credential.get_token, f"{AZURE_MANAGEMENT}/.default")
            async with self._client_factory(timeout=60) as client:
                response = await client.request(
                    method,
                    url,
                    params={"api-version": api_version},
                    headers={"Authorization": f"Bearer {token.token}"},
                    json=body,
                )
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
                return payload
        except FinOpsQueryError:
            raise
        except Exception as exc:
            raise FinOpsQueryError(f"Azure request failed: {type(exc).__name__}") from exc

    async def forecast(self, start: date, end: date) -> ForecastResult:
        payload = await self._request(
            "POST",
            "/providers/Microsoft.CostManagement/forecast",
            "2023-03-01",
            {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {"from": _utc(start), "to": _utc(end)},
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
                },
                "includeActualCost": False,
                "includeFreshPartialCost": False,
            },
        )
        columns, rows = _table(payload)
        cost_index = _column(columns, "Cost", "PreTaxCost")
        currency_index = columns.index("Currency") if "Currency" in columns else None
        amount = sum((Decimal(str(row[cost_index] or "0")) for row in rows), Decimal("0"))
        currency = str(rows[0][currency_index]) if rows and currency_index is not None else "USD"
        return ForecastResult(
            provider_name=self.name,
            amount=amount,
            currency=currency,
            start_date=start,
            end_date=end,
        )

    async def daily_costs(self, start: date, end: date) -> tuple[list[tuple[date, Decimal]], str]:
        payload = await self._request(
            "POST",
            "/providers/Microsoft.CostManagement/query",
            "2025-03-01",
            {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {"from": _utc(start), "to": _utc(end)},
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                },
            },
        )
        columns, rows = _table(payload)
        cost_index = _column(columns, "PreTaxCost", "Cost")
        date_index = _column(columns, "UsageDate", "BillingMonth")
        currency_index = columns.index("Currency") if "Currency" in columns else None
        daily: dict[date, Decimal] = {}
        for row in rows:
            day = _azure_date(row[date_index])
            daily[day] = daily.get(day, Decimal("0")) + Decimal(str(row[cost_index] or "0"))
        currency = str(rows[0][currency_index]) if rows and currency_index is not None else "USD"
        return sorted(daily.items()), currency

    async def anomalies(self, start: date, end: date) -> list[CostAnomaly]:
        # Azure has no query API for anomaly alerts, so detect them from daily cost
        # with a 28-day lookback before the requested window.
        daily, currency = await self.daily_costs(start - timedelta(days=28), end)
        return [
            anomaly
            for anomaly in detect_anomalies(self.name, daily, currency)
            if anomaly.start_date >= start
        ]

    async def budgets(self) -> list[BudgetStatus]:
        payload = await self._request(
            "GET", "/providers/Microsoft.Consumption/budgets", "2023-05-01"
        )
        budgets: list[BudgetStatus] = []
        for item in payload.get("value", []):
            properties = item.get("properties", {})
            current = properties.get("currentSpend") or {}
            forecast = properties.get("forecastSpend") or {}
            budgets.append(
                BudgetStatus(
                    provider_name=self.name,
                    name=str(item.get("name", "")),
                    limit=Decimal(str(properties.get("amount", "0"))),
                    actual=Decimal(str(current.get("amount", "0"))),
                    forecast=(Decimal(str(forecast["amount"])) if "amount" in forecast else None),
                    currency=str(current.get("unit", "USD")),
                    time_grain=properties.get("timeGrain"),
                )
            )
        return budgets

    async def cost_by_tag(self, tag_key: str, start: date, end: date) -> list[TagCost]:
        payload = await self._request(
            "POST",
            "/providers/Microsoft.CostManagement/query",
            "2025-03-01",
            {
                "type": "ActualCost",
                "timeframe": "Custom",
                "timePeriod": {"from": _utc(start), "to": _utc(end)},
                "dataset": {
                    "granularity": "None",
                    "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                    "grouping": [{"type": "TagKey", "name": tag_key}],
                },
            },
        )
        columns, rows = _table(payload)
        cost_index = _column(columns, "PreTaxCost", "Cost")
        value_index = columns.index("TagValue") if "TagValue" in columns else None
        currency_index = columns.index("Currency") if "Currency" in columns else None
        totals: dict[tuple[str, str], Decimal] = {}
        for row in rows:
            value = str(row[value_index] or "") if value_index is not None else ""
            currency = str(row[currency_index]) if currency_index is not None else "USD"
            key = (value or "(untagged)", currency)
            totals[key] = totals.get(key, Decimal("0")) + Decimal(str(row[cost_index] or "0"))
        return [
            TagCost(
                provider_name=self.name,
                tag_key=tag_key,
                tag_value=value,
                amount=amount,
                currency=currency,
            )
            for (value, currency), amount in totals.items()
        ]


def _table(payload: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    properties = payload.get("properties", {})
    columns = [str(column.get("name")) for column in properties.get("columns", [])]
    return columns, list(properties.get("rows", []))


def _column(columns: list[str], *names: str) -> int:
    for name in names:
        if name in columns:
            return columns.index(name)
    raise FinOpsQueryError(f"Azure response is missing column {names[0]}")


def _azure_date(value: Any) -> date:
    text = str(value)
    if text.isdigit() and len(text) == 8:
        return date(int(text[:4]), int(text[4:6]), int(text[6:]))
    return date.fromisoformat(text[:10])


def _utc(value: date) -> str:
    return (
        datetime(value.year, value.month, value.day, tzinfo=UTC).isoformat().replace("+00:00", "Z")
    )


def _optional_decimal(value: Any) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None
