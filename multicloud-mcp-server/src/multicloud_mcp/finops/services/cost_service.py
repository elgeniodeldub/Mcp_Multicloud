"""FinOps orchestration service with concurrent live queries and short caching."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

import structlog

from multicloud_mcp.cache import ToolsCache
from multicloud_mcp.finops.enums import FinOpsDimension
from multicloud_mcp.finops.exceptions import FinOpsProviderUnavailableError
from multicloud_mcp.finops.models import FinOpsCostResult, FinOpsQuery
from multicloud_mcp.finops.providers.aws import AWSFinOpsProvider
from multicloud_mcp.finops.providers.azure import AzureFinOpsProvider
from multicloud_mcp.finops.providers.base import FinOpsProvider

logger = structlog.get_logger()


@dataclass
class CostQueryResponse:
    """Results plus operational metadata for a multi-provider query."""

    results: list[FinOpsCostResult]
    providers_failed: list[str]
    cache_hit: bool = False
    duration_ms: float = 0.0

    @property
    def partial(self) -> bool:
        return bool(self.providers_failed)


class FinOpsCostService:
    """Coordinate provider adapters; tools never call cloud SDKs directly."""

    def __init__(
        self,
        providers: Mapping[str, FinOpsProvider] | None = None,
        cache: ToolsCache | None = None,
        cache_ttl: float = 300.0,
    ) -> None:
        self.providers: dict[str, FinOpsProvider] = dict(
            providers or {"aws": AWSFinOpsProvider(), "azure": AzureFinOpsProvider()}
        )
        self.cache = cache or ToolsCache(default_ttl=cache_ttl)
        self.cache_ttl = cache_ttl

    async def query(self, query: FinOpsQuery) -> CostQueryResponse:
        """Query selected providers concurrently and preserve partial results."""
        cached = self.cache.get(query.cache_key)
        if isinstance(cached, CostQueryResponse):
            return CostQueryResponse(
                results=cached.results,
                providers_failed=cached.providers_failed,
                cache_hit=True,
                duration_ms=0.0,
            )
        selected = query.providers or list(self.providers)
        unknown = [provider for provider in selected if provider not in self.providers]
        if unknown:
            raise FinOpsProviderUnavailableError(
                f"Unsupported FinOps provider(s): {', '.join(unknown)}"
            )
        started = time.perf_counter()
        responses = await asyncio.gather(
            *(self._query_provider(self.providers[name], query) for name in selected),
            return_exceptions=True,
        )
        results: list[FinOpsCostResult] = []
        failed: list[str] = []
        for name, response in zip(selected, responses, strict=True):
            if isinstance(response, BaseException):
                failed.append(name)
                logger.warning(
                    "finops_provider_query_failed", provider=name, error=type(response).__name__
                )
            else:
                results.extend(response)
        outcome = CostQueryResponse(
            results=results,
            providers_failed=failed,
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        self.cache.set(query.cache_key, outcome, ttl=self.cache_ttl)
        logger.info(
            "finops_query_completed",
            providers=selected,
            metric=query.metric.value,
            dimensions=[dimension.value for dimension in query.group_by],
            start_date=query.start_date.isoformat(),
            end_date=query.end_date.isoformat(),
            duration_ms=round(outcome.duration_ms, 2),
            cache_hit=False,
            number_of_rows=len(results),
        )
        return outcome

    @staticmethod
    async def _query_provider(
        provider: FinOpsProvider, query: FinOpsQuery
    ) -> list[FinOpsCostResult]:
        results = await provider.query_cost(query)
        return [FinOpsCostService._normalize_result(result, query.group_by) for result in results]

    @staticmethod
    def _normalize_result(
        result: FinOpsCostResult, dimensions: list[FinOpsDimension]
    ) -> FinOpsCostResult:
        from multicloud_mcp.finops.services.service_category import normalize_service_category

        if result.service_category is None and result.service_name:
            result.service_category = normalize_service_category(
                result.provider_name, result.service_name
            )
        if not dimensions:
            result.service_name = None
            result.service_category = None
            result.region_id = None
            result.sub_account_id = result.sub_account_id
        return result

    @staticmethod
    def aggregate_by_currency(results: list[FinOpsCostResult]) -> dict[str, Decimal]:
        """Aggregate effective cost without ever mixing currencies."""
        totals: dict[str, Decimal] = {}
        for result in results:
            totals[result.currency] = (
                totals.get(result.currency, Decimal("0")) + result.effective_cost
            )
        return totals
