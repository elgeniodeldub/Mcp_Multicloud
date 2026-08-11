"""MCP tool for deterministic FinOps period/provider comparisons."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from decimal import Decimal
from typing import Any

from multicloud_mcp.finops.models import FinOpsQuery
from multicloud_mcp.finops.services.cost_service import FinOpsCostService
from multicloud_mcp.finops.services.query_planner import FinOpsQueryPlanner
from multicloud_mcp.finops.tools._common import money
from multicloud_mcp.providers.base import ToolInfo


class FinOpsCompareTool:
    """Compare current and previous periods without floating-point arithmetic."""

    def __init__(self, service: FinOpsCostService | None = None) -> None:
        self.service = service or FinOpsCostService()
        self.planner = FinOpsQueryPlanner()

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="finops__compare",
            description=(
                "Read-only deterministic comparison of AWS/Azure live costs between "
                "providers or periods. Use for spend differences and percentages, not "
                "public list prices; GCP actual cost is unsupported. Returns absolute "
                "and percentage differences without LLM calculations."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "compare_start_date": {"type": "string"},
                    "compare_end_date": {"type": "string"},
                    "period": {"type": "string", "enum": ["current_month", "month_to_date"]},
                    "metric": {"type": "string", "enum": ["effective_cost", "billed_cost"]},
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                },
            },
            original_name="finops__compare",
            provider="finops",
            namespace="finops",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        current = self.planner.plan(arguments)
        previous = self._previous_query(current, arguments)
        current_response, previous_response = await asyncio.gather(
            self.service.query(current), self.service.query(previous)
        )
        current_totals = self._totals(current_response.results)
        previous_totals = self._totals(previous_response.results)
        current_provider_totals = self._provider_totals(current_response.results)
        previous_provider_totals = self._provider_totals(previous_response.results)
        currencies = sorted(set(current_totals) | set(previous_totals))
        comparisons = []
        for currency in currencies:
            current_value = current_totals.get(currency, Decimal("0"))
            previous_value = previous_totals.get(currency, Decimal("0"))
            delta = current_value - previous_value
            percentage = None if previous_value == 0 else (delta / previous_value) * Decimal("100")
            comparisons.append(
                {
                    "currency": currency,
                    "current_cost": money(current_value),
                    "previous_cost": money(previous_value),
                    "absolute_difference": money(delta),
                    "percentage_difference": money(percentage) if percentage is not None else None,
                }
            )
        return {
            "comparisons": comparisons,
            "provider_comparison": self._provider_comparison(
                current_provider_totals, previous_provider_totals
            ),
            "currency_mismatch": len(currencies) > 1,
            "current_period": {
                "start": current.start_date.isoformat(),
                "end": current.end_date.isoformat(),
            },
            "previous_period": {
                "start": previous.start_date.isoformat(),
                "end": previous.end_date.isoformat(),
            },
            "partial": current_response.partial or previous_response.partial,
            "providers_failed": sorted(
                set(current_response.providers_failed + previous_response.providers_failed)
            ),
            "cache_hit": current_response.cache_hit and previous_response.cache_hit,
        }

    def _previous_query(self, current: FinOpsQuery, arguments: dict[str, Any]) -> FinOpsQuery:
        if arguments.get("compare_start_date") and arguments.get("compare_end_date"):
            return self.planner.plan(
                {
                    **arguments,
                    "start_date": arguments["compare_start_date"],
                    "end_date": arguments["compare_end_date"],
                    "period": None,
                }
            )
        duration = current.end_date - current.start_date
        return current.model_copy(
            update={"start_date": current.start_date - duration, "end_date": current.start_date}
        )

    @staticmethod
    def _totals(results: list[Any]) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = defaultdict(Decimal)
        for result in results:
            totals[result.currency] += result.effective_cost
        return dict(totals)

    @staticmethod
    def _provider_totals(results: list[Any]) -> dict[tuple[str, str], Decimal]:
        totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for result in results:
            totals[(result.provider_name, result.currency)] += result.effective_cost
        return dict(totals)

    @staticmethod
    def _provider_comparison(
        current: dict[tuple[str, str], Decimal], previous: dict[tuple[str, str], Decimal]
    ) -> list[dict[str, str | None]]:
        keys = sorted(set(current) | set(previous))
        return [
            {
                "provider": provider,
                "currency": currency,
                "current_cost": money(current.get((provider, currency), Decimal("0"))),
                "previous_cost": money(previous.get((provider, currency), Decimal("0"))),
            }
            for provider, currency in keys
        ]
