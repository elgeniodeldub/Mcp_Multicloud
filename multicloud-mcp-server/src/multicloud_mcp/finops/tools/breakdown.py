"""MCP tool for normalized cost breakdowns."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from multicloud_mcp.finops.enums import FinOpsDimension
from multicloud_mcp.finops.services.cost_service import FinOpsCostService
from multicloud_mcp.finops.services.query_planner import FinOpsQueryPlanner
from multicloud_mcp.finops.tools._common import money, response_metadata, result_dimension
from multicloud_mcp.providers.base import ToolInfo


class FinOpsBreakdownTool:
    """Group live costs by one normalized dimension."""

    def __init__(self, service: FinOpsCostService | None = None) -> None:
        self.service = service or FinOpsCostService()
        self.planner = FinOpsQueryPlanner()

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="finops__breakdown",
            description="Break down live AWS and Azure costs by provider, account, service, category, or region.",
            input_schema={
                "type": "object",
                "required": ["group_by"],
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "period": {"type": "string"},
                    "metric": {"type": "string", "enum": ["effective_cost", "billed_cost"]},
                    "group_by": {
                        "type": "string",
                        "enum": [dimension.value for dimension in FinOpsDimension],
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                    "limit": {"type": "integer", "minimum": 1},
                },
            },
            original_name="finops__breakdown",
            provider="finops",
            namespace="finops",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raw_dimension = arguments.get("group_by", FinOpsDimension.SERVICE.value)
        dimension = FinOpsDimension(str(raw_dimension).lower())
        query = self.planner.plan({**arguments, "group_by": [dimension]})
        response = await self.service.query(query)
        grouped: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for result in response.results:
            grouped[(result_dimension(result, dimension.value), result.currency)] += (
                result.effective_cost
            )
        groups = [
            {"dimension": key, "effective_cost": money(value), "currency": currency}
            for (key, currency), value in sorted(grouped.items())
        ]
        return {
            "group_by": dimension.value,
            "groups": groups,
            "currency_mismatch": len({currency for _, currency in grouped}) > 1,
            "period": {"start": query.start_date.isoformat(), "end": query.end_date.isoformat()},
            "metric": query.metric.value,
            **response_metadata(response),
        }
