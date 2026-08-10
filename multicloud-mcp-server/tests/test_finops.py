"""Unit and integration-style tests for live FinOps normalization."""

import asyncio
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from multicloud_mcp.finops.enums import CostMetric, FinOpsDimension
from multicloud_mcp.finops.models import FinOpsCostResult, FinOpsQuery
from multicloud_mcp.finops.providers.aws import AWSFinOpsProvider
from multicloud_mcp.finops.providers.azure import AzureFinOpsProvider
from multicloud_mcp.finops.services.cost_service import FinOpsCostService
from multicloud_mcp.finops.services.service_category import normalize_service_category
from multicloud_mcp.finops.tools.breakdown import FinOpsBreakdownTool
from multicloud_mcp.finops.tools.compare import FinOpsCompareTool
from multicloud_mcp.finops.tools.get_cost import FinOpsGetCostTool


def query(**values: Any) -> FinOpsQuery:
    return FinOpsQuery(
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
        **values,
    )


class FakeCostExplorer:
    def __init__(self, metric: str = "NetAmortizedCost") -> None:
        self.metric = metric
        self.calls: list[dict[str, Any]] = []

    def get_cost_and_usage(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2026-07-01", "End": "2026-08-01"},
                    "Groups": [
                        {
                            "Keys": ["Amazon EC2"],
                            "Metrics": {self.metric: {"Amount": "12.34", "Unit": "USD"}},
                        }
                    ],
                }
            ]
        }


@pytest.mark.asyncio
async def test_aws_provider_pushes_service_grouping_and_uses_decimal() -> None:
    client = FakeCostExplorer()
    provider = AWSFinOpsProvider(client_factory=lambda: client)
    results = await provider.query_cost(query(group_by=[FinOpsDimension.SERVICE]))
    assert client.calls[0]["GroupBy"] == [{"Type": "DIMENSION", "Key": "SERVICE"}]
    assert client.calls[0]["Metrics"] == ["NetAmortizedCost"]
    assert results[0].effective_cost == Decimal("12.34")
    assert results[0].service_name == "Amazon EC2"


class FakeToken:
    token = "test-token"


class FakeCredential:
    def get_token(self, scope: str) -> FakeToken:
        assert scope.endswith(".default")
        return FakeToken()


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "properties": {
                "columns": [
                    {"name": "SubscriptionId"},
                    {"name": "ServiceName"},
                    {"name": "PreTaxCost"},
                    {"name": "Currency"},
                ],
                "rows": [["sub-1", "Virtual Machines", 5.5, "USD"]],
            }
        }


class FakeAsyncClient:
    def __init__(self, **_: Any) -> None:
        self.body: dict[str, Any] | None = None

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        return None

    async def post(self, _url: str, **kwargs: Any) -> FakeResponse:
        self.body = kwargs["json"]
        return FakeResponse()


@pytest.mark.asyncio
async def test_azure_provider_maps_dimensions_and_amortized_metric() -> None:
    client = FakeAsyncClient()
    provider = AzureFinOpsProvider(
        subscription_id="sub-1",
        credential=FakeCredential(),
        client_factory=lambda **kwargs: client,
    )
    results = await provider.query_cost(query(group_by=[FinOpsDimension.SERVICE]))
    assert client.body is not None
    assert client.body["type"] == "AmortizedCost"
    assert client.body["dataset"]["grouping"] == [{"type": "Dimension", "name": "ServiceName"}]
    assert results[0].service_name == "Virtual Machines"
    assert results[0].effective_cost == Decimal("5.5")


@pytest.mark.asyncio
async def test_finops_service_queries_providers_concurrently_and_caches() -> None:
    class SlowProvider:
        def __init__(self, name: str, delay: float, amount: str) -> None:
            self.name = name
            self.delay = delay
            self.amount = amount
            self.calls = 0

        async def query_cost(self, _: FinOpsQuery) -> list[FinOpsCostResult]:
            self.calls += 1
            await asyncio.sleep(self.delay)
            return [
                FinOpsCostResult(
                    provider_name=self.name,
                    effective_cost=Decimal(self.amount),
                    currency="USD",
                    start_date=date(2026, 7, 1),
                    end_date=date(2026, 8, 1),
                )
            ]

    aws = SlowProvider("aws", 0.03, "10")
    azure = SlowProvider("azure", 0.03, "20")
    service = FinOpsCostService({"aws": aws, "azure": azure})
    started = asyncio.get_running_loop().time()
    first = await service.query(query())
    duration = asyncio.get_running_loop().time() - started
    second = await service.query(query())
    assert duration < 0.055
    assert sum(result.effective_cost for result in first.results) == Decimal("30")
    assert second.cache_hit is True
    assert aws.calls == azure.calls == 1


@pytest.mark.asyncio
async def test_finops_tools_do_not_sum_currency_mismatch_and_compare_exactly() -> None:
    class StaticProvider:
        def __init__(self, name: str, currency: str, amount: str) -> None:
            self.name, self.currency, self.amount = name, currency, amount

        async def query_cost(self, current: FinOpsQuery) -> list[FinOpsCostResult]:
            return [
                FinOpsCostResult(
                    provider_name=self.name,
                    service_name="Amazon EC2",
                    effective_cost=Decimal(self.amount),
                    currency=self.currency,
                    start_date=current.start_date,
                    end_date=current.end_date,
                )
            ]

    service = FinOpsCostService(
        {"aws": StaticProvider("aws", "USD", "100"), "azure": StaticProvider("azure", "BRL", "200")}
    )
    total = await FinOpsGetCostTool(service).execute(
        {"start_date": "2026-07-01", "end_date": "2026-08-01"}
    )
    breakdown = await FinOpsBreakdownTool(service).execute(
        {"start_date": "2026-07-01", "end_date": "2026-08-01", "group_by": "service"}
    )
    assert total["currency_mismatch"] is True
    assert total["total_effective_cost"] == {"BRL": "200", "USD": "100"}
    assert len(breakdown["groups"]) == 2

    compare_service = FinOpsCostService({"aws": StaticProvider("aws", "USD", "125")})
    comparison = await FinOpsCompareTool(compare_service).execute(
        {
            "start_date": "2026-08-01",
            "end_date": "2026-09-01",
            "compare_start_date": "2026-07-01",
            "compare_end_date": "2026-08-01",
            "providers": ["aws"],
        }
    )
    assert comparison["comparisons"][0]["absolute_difference"] == "0"


def test_service_category_and_cache_key() -> None:
    assert normalize_service_category("aws", "Amazon EC2") == "Compute"
    assert normalize_service_category("azure", "Azure Blob Storage") == "Storage"
    assert normalize_service_category("aws", "Unmapped Service") == "Other"
    assert query(metric=CostMetric.BILLED, group_by=[FinOpsDimension.ACCOUNT]).cache_key.endswith(
        ":billed_cost:account:"
    )
