"""MCP tool for normalized live cost totals."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from multicloud_mcp.finops.services.cost_service import FinOpsCostService
from multicloud_mcp.finops.services.query_planner import FinOpsQueryPlanner
from multicloud_mcp.finops.tools._common import money, response_metadata
from multicloud_mcp.providers.base import ToolInfo


class FinOpsGetCostTool:
    """Return effective or billed cost totals by provider and currency."""

    def __init__(self, service: FinOpsCostService | None = None) -> None:
        self.service = service or FinOpsCostService()
        self.planner = FinOpsQueryPlanner()

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="finops__get_cost",
            description="Get normalized live AWS and Azure cost totals using a FOCUS-aligned domain model.",
            input_schema=self._schema(),
            original_name="finops__get_cost",
            provider="finops",
            namespace="finops",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = self.planner.plan(arguments)
        response = await self.service.query(query)
        by_provider: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
        for result in response.results:
            by_provider[result.provider_name][result.currency] += result.effective_cost
        totals: dict[str, Decimal] = defaultdict(Decimal)
        for currencies in by_provider.values():
            for currency, value in currencies.items():
                totals[currency] += value
        total_value: str | dict[str, str]
        if len(totals) == 1:
            total_value = money(next(iter(totals.values())))
            currency_value: str | None = next(iter(totals))
        else:
            total_value = {key: money(value) for key, value in sorted(totals.items())}
            currency_value = None
        providers = [
            {
                "provider": provider,
                "effective_cost": (
                    money(next(iter(currencies.values())))
                    if len(currencies) == 1
                    else {key: money(value) for key, value in sorted(currencies.items())}
                ),
                "currency": next(iter(currencies)) if len(currencies) == 1 else None,
            }
            for provider, currencies in sorted(by_provider.items())
        ]
        output: dict[str, Any] = {
            "total_effective_cost": total_value,
            "currency": currency_value,
            "providers": providers,
            "period": {"start": query.start_date.isoformat(), "end": query.end_date.isoformat()},
            "metric": query.metric.value,
            "currency_mismatch": len(totals) > 1,
        }
        output.update(response_metadata(response))
        return output

    @staticmethod
    def _schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Inclusive YYYY-MM-DD."},
                "end_date": {"type": "string", "description": "Exclusive YYYY-MM-DD."},
                "period": {
                    "type": "string",
                    "enum": [
                        "month_to_date",
                        "last_7_days",
                        "last_30_days",
                        "previous_month",
                        "current_month",
                    ],
                },
                "metric": {
                    "type": "string",
                    "enum": ["effective_cost", "billed_cost"],
                    "default": "effective_cost",
                },
                "providers": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["aws", "azure"]},
                },
            },
        }
