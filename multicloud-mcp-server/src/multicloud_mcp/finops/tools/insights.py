"""MCP tools for cost forecasts, anomalies, budgets, and tag allocation."""

from __future__ import annotations

import asyncio
import calendar
from collections.abc import Awaitable, Callable, Mapping
from datetime import date, timedelta
from typing import Any, Protocol, TypeVar

import structlog

from multicloud_mcp.finops.exceptions import FinOpsQueryError
from multicloud_mcp.finops.models import period_dates
from multicloud_mcp.finops.providers.insights import (
    AWSInsightsProvider,
    AzureInsightsProvider,
    BudgetStatus,
    CostAnomaly,
    ForecastResult,
    TagCost,
)
from multicloud_mcp.finops.tools._common import money
from multicloud_mcp.providers.base import ToolInfo

logger = structlog.get_logger()

T = TypeVar("T")

PROVIDERS_SCHEMA = {"type": "array", "items": {"type": "string", "enum": ["aws", "azure"]}}


class InsightsProvider(Protocol):
    """Contract implemented by AWS and Azure insight adapters."""

    name: str

    async def forecast(self, start: date, end: date) -> ForecastResult: ...

    async def anomalies(self, start: date, end: date) -> list[CostAnomaly]: ...

    async def budgets(self) -> list[BudgetStatus]: ...

    async def cost_by_tag(self, tag_key: str, start: date, end: date) -> list[TagCost]: ...


class FinOpsInsightsService:
    """Fan out insight calls to providers and keep partial results."""

    def __init__(self, providers: Mapping[str, InsightsProvider] | None = None) -> None:
        self.providers: dict[str, InsightsProvider] = dict(
            providers or {"aws": AWSInsightsProvider(), "azure": AzureInsightsProvider()}
        )

    def select(self, arguments: dict[str, Any]) -> list[str]:
        raw = arguments.get("providers") or list(self.providers)
        selected = [str(item).lower() for item in ([raw] if isinstance(raw, str) else raw)]
        unknown = [name for name in selected if name not in self.providers]
        if unknown:
            raise FinOpsQueryError(f"Unsupported provider(s): {', '.join(unknown)}")
        return selected

    async def gather(
        self,
        selected: list[str],
        call: Callable[[InsightsProvider], Awaitable[T]],
    ) -> tuple[dict[str, T], list[str]]:
        responses = await asyncio.gather(
            *(call(self.providers[name]) for name in selected), return_exceptions=True
        )
        results: dict[str, T] = {}
        failed: list[str] = []
        for name, response in zip(selected, responses, strict=True):
            if isinstance(response, BaseException):
                failed.append(name)
                logger.warning(
                    "finops_insight_failed", provider=name, error=type(response).__name__
                )
            else:
                results[name] = response
        return results, failed


def _dates(arguments: dict[str, Any], default_period: str) -> tuple[date, date]:
    try:
        if arguments.get("start_date") and arguments.get("end_date"):
            start = date.fromisoformat(str(arguments["start_date"]))
            end = date.fromisoformat(str(arguments["end_date"]))
        else:
            start, end = period_dates(str(arguments.get("period", default_period)))
    except ValueError as exc:
        raise FinOpsQueryError("Invalid date parameters") from exc
    if end <= start:
        raise FinOpsQueryError("end_date must be later than start_date")
    return start, end


def _info(name: str, description: str, properties: dict[str, Any], **extra: Any) -> ToolInfo:
    return ToolInfo(
        name=name,
        description=description,
        input_schema={"type": "object", "properties": properties, **extra},
        original_name=name,
        provider="finops",
        namespace="finops",
    )


class FinOpsForecastTool:
    """Forecast spend until a future date (default: end of the current month)."""

    def __init__(self, service: FinOpsInsightsService) -> None:
        self.service = service

    def get_tool_info(self) -> ToolInfo:
        return _info(
            "finops__forecast",
            "Read-only spend forecast from AWS Cost Explorer and Azure Cost Management. "
            "Defaults to tomorrow through the end of the current month. Forecasts are "
            "provider estimates, not invoices.",
            {
                "start_date": {"type": "string", "description": "YYYY-MM-DD, today or later."},
                "end_date": {"type": "string", "description": "Exclusive YYYY-MM-DD."},
                "providers": PROVIDERS_SCHEMA,
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        today = date.today()
        if arguments.get("start_date") or arguments.get("end_date"):
            start, end = _dates(arguments, "current_month")
        else:
            last_day = calendar.monthrange(today.year, today.month)[1]
            start = today + timedelta(days=1)
            end = today.replace(day=last_day) + timedelta(days=1)
            if start >= end:
                end = start + timedelta(days=1)
        if start < today:
            raise FinOpsQueryError("Forecast start_date cannot be in the past")
        selected = self.service.select(arguments)
        results, failed = await self.service.gather(selected, lambda p: p.forecast(start, end))
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "cost_basis": "forecast",
            "forecasts": [
                {
                    "provider": result.provider_name,
                    "amount": money(result.amount),
                    "currency": result.currency,
                    "lower_bound": money(result.lower_bound) if result.lower_bound else None,
                    "upper_bound": money(result.upper_bound) if result.upper_bound else None,
                }
                for result in results.values()
            ],
            "partial": bool(failed),
            "providers_failed": failed,
        }


class FinOpsAnomaliesTool:
    """List cost anomalies for a period."""

    def __init__(self, service: FinOpsInsightsService) -> None:
        self.service = service

    def get_tool_info(self) -> ToolInfo:
        return _info(
            "finops__anomalies",
            "Read-only cost anomaly report. AWS uses Cost Anomaly Detection monitors; "
            "Azure uses a robust statistical baseline (median/MAD over 28 days of daily "
            "actual cost) because Azure exposes no anomaly query API. Defaults to the last "
            "30 days.",
            {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "period": {"type": "string", "enum": ["last_7_days", "last_30_days"]},
                "min_impact": {"type": "number", "minimum": 0, "default": 0},
                "providers": PROVIDERS_SCHEMA,
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        start, end = _dates(arguments, "last_30_days")
        min_impact = float(arguments.get("min_impact", 0) or 0)
        selected = self.service.select(arguments)
        results, failed = await self.service.gather(selected, lambda p: p.anomalies(start, end))
        anomalies = sorted(
            (
                item
                for items in results.values()
                for item in items
                if abs(float(item.impact)) >= min_impact
            ),
            key=lambda item: abs(item.impact),
            reverse=True,
        )
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "anomalies": [
                {
                    **item.model_dump(mode="json", exclude_none=True),
                    "impact": money(item.impact),
                }
                for item in anomalies
            ],
            "count": len(anomalies),
            "partial": bool(failed),
            "providers_failed": failed,
        }


class FinOpsBudgetsTool:
    """Report budgets and their utilization."""

    def __init__(self, service: FinOpsInsightsService) -> None:
        self.service = service

    def get_tool_info(self) -> ToolInfo:
        return _info(
            "finops__budgets",
            "Read-only budget status from AWS Budgets and Azure Consumption budgets: "
            "limit, actual spend, forecast, and utilization percentage. Flags budgets "
            "at or above the alert threshold.",
            {
                "alert_threshold_pct": {"type": "number", "minimum": 0, "default": 80},
                "providers": PROVIDERS_SCHEMA,
            },
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        threshold = float(arguments.get("alert_threshold_pct", 80))
        selected = self.service.select(arguments)
        results, failed = await self.service.gather(selected, lambda p: p.budgets())
        budgets = []
        for items in results.values():
            for budget in items:
                utilization = float(budget.utilization)
                forecast_pct = (
                    float(budget.forecast / budget.limit * 100)
                    if budget.forecast is not None and budget.limit
                    else None
                )
                budgets.append(
                    {
                        "provider": budget.provider_name,
                        "name": budget.name,
                        "limit": money(budget.limit),
                        "actual": money(budget.actual),
                        "forecast": money(budget.forecast) if budget.forecast is not None else None,
                        "currency": budget.currency,
                        "time_grain": budget.time_grain,
                        "utilization_pct": round(utilization, 2),
                        "forecast_pct": round(forecast_pct, 2) if forecast_pct else None,
                        "alert": utilization >= threshold
                        or (forecast_pct is not None and forecast_pct >= 100),
                    }
                )
        budgets.sort(key=lambda item: float(str(item["utilization_pct"])), reverse=True)
        return {
            "budgets": budgets,
            "alerts": sum(1 for item in budgets if item["alert"]),
            "partial": bool(failed),
            "providers_failed": failed,
        }


class FinOpsCostByTagTool:
    """Allocate spend by a tag key."""

    def __init__(self, service: FinOpsInsightsService) -> None:
        self.service = service

    def get_tool_info(self) -> ToolInfo:
        return _info(
            "finops__cost_by_tag",
            "Read-only actual spend grouped by the values of one tag key (for example "
            "'environment', 'team', 'cost-center'). On AWS the tag must be activated as a "
            "cost allocation tag. Untagged spend is reported as '(untagged)'.",
            {
                "tag_key": {"type": "string", "minLength": 1, "maxLength": 128},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "period": {"type": "string"},
                "providers": PROVIDERS_SCHEMA,
            },
            required=["tag_key"],
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        tag_key = str(arguments.get("tag_key", "")).strip()
        if not tag_key or len(tag_key) > 128:
            raise FinOpsQueryError("tag_key is required (max 128 characters)")
        start, end = _dates(arguments, "month_to_date")
        selected = self.service.select(arguments)
        results, failed = await self.service.gather(
            selected, lambda p: p.cost_by_tag(tag_key, start, end)
        )
        rows = sorted(
            (item for items in results.values() for item in items),
            key=lambda item: item.amount,
            reverse=True,
        )
        return {
            "tag_key": tag_key,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "groups": [
                {
                    "provider": item.provider_name,
                    "tag_value": item.tag_value,
                    "amount": money(item.amount),
                    "currency": item.currency,
                }
                for item in rows
            ],
            "partial": bool(failed),
            "providers_failed": failed,
        }
