"""Input planning and date helpers for FinOps tools."""

from datetime import date
from typing import Any

from multicloud_mcp.finops.enums import CostMetric, FinOpsDimension
from multicloud_mcp.finops.exceptions import FinOpsQueryError
from multicloud_mcp.finops.models import FinOpsQuery, period_dates


class FinOpsQueryPlanner:
    """Translate MCP arguments into a validated provider-independent query."""

    def plan(
        self, arguments: dict[str, Any], default_group_by: list[FinOpsDimension] | None = None
    ) -> FinOpsQuery:
        try:
            start, end = self._dates(arguments)
            raw_dimensions = arguments.get("group_by", default_group_by or [])
            if isinstance(raw_dimensions, str):
                raw_dimensions = [raw_dimensions]
            dimensions = [FinOpsDimension(str(item).lower()) for item in raw_dimensions]
            if (
                FinOpsDimension.SERVICE_CATEGORY in dimensions
                and FinOpsDimension.SERVICE not in dimensions
            ):
                # Category is normalized locally from provider service names; push SERVICE down first.
                dimensions.append(FinOpsDimension.SERVICE)
            providers = arguments.get("providers")
            if providers is not None:
                if isinstance(providers, str):
                    providers = [providers]
                providers = [str(provider).lower() for provider in providers]
            metric = CostMetric(str(arguments.get("metric", CostMetric.EFFECTIVE.value)).lower())
            return FinOpsQuery(
                start_date=start,
                end_date=end,
                metric=metric,
                group_by=dimensions,
                providers=providers,
                limit=arguments.get("limit"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FinOpsQueryError("Invalid FinOps query parameters") from exc

    @staticmethod
    def _dates(arguments: dict[str, Any]) -> tuple[date, date]:
        period = arguments.get("period")
        if period:
            return period_dates(str(period))
        start = date.fromisoformat(str(arguments["start_date"]))
        end = date.fromisoformat(str(arguments["end_date"]))
        return start, end
