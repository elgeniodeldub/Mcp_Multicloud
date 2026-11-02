"""Tests for forecast, anomaly, budget, and tag-cost FinOps insights."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest

from multicloud_mcp.finops.exceptions import FinOpsQueryError
from multicloud_mcp.finops.providers.insights import (
    AWSInsightsProvider,
    AzureInsightsProvider,
    BudgetStatus,
    CostAnomaly,
    ForecastResult,
    TagCost,
    detect_anomalies,
)
from multicloud_mcp.finops.tools.insights import (
    FinOpsAnomaliesTool,
    FinOpsBudgetsTool,
    FinOpsCostByTagTool,
    FinOpsForecastTool,
    FinOpsInsightsService,
)


class FakeCE:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get_cost_forecast(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("forecast", kwargs))
        return {
            "Total": {"Amount": "120.50", "Unit": "USD"},
            "ForecastResultsByTime": [
                {"PredictionIntervalLowerBound": "100", "PredictionIntervalUpperBound": "140"}
            ],
        }

    def get_anomalies(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("anomalies", kwargs))
        if "NextPageToken" not in kwargs:
            return {
                "Anomalies": [
                    {
                        "AnomalyStartDate": "2026-10-10",
                        "DimensionValue": "Amazon EC2",
                        "Impact": {"TotalImpact": 42.5, "TotalActualSpend": 60},
                        "AnomalyScore": {"MaxScore": 0.9},
                        "RootCauses": [{"Service": "Amazon EC2", "Region": "us-east-1"}],
                    }
                ],
                "NextPageToken": "page2",
            }
        return {"Anomalies": []}

    def get_cost_and_usage(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("usage", kwargs))
        return {
            "ResultsByTime": [
                {
                    "Groups": [
                        {
                            "Keys": ["team$platform"],
                            "Metrics": {"UnblendedCost": {"Amount": "10", "Unit": "USD"}},
                        },
                        {
                            "Keys": ["team$"],
                            "Metrics": {"UnblendedCost": {"Amount": "3", "Unit": "USD"}},
                        },
                    ]
                }
            ]
        }


class FakeBudgets:
    def describe_budgets(self, **kwargs: Any) -> dict[str, Any]:
        assert kwargs["AccountId"] == "123456789012"
        return {
            "Budgets": [
                {
                    "BudgetName": "monthly",
                    "BudgetLimit": {"Amount": "100", "Unit": "USD"},
                    "CalculatedSpend": {
                        "ActualSpend": {"Amount": "85", "Unit": "USD"},
                        "ForecastedSpend": {"Amount": "110", "Unit": "USD"},
                    },
                    "TimeUnit": "MONTHLY",
                }
            ]
        }


class FakeSTS:
    def get_caller_identity(self) -> dict[str, str]:
        return {"Account": "123456789012"}


def aws() -> tuple[AWSInsightsProvider, FakeCE]:
    ce = FakeCE()
    return (
        AWSInsightsProvider(
            ce_factory=lambda: ce,
            budgets_factory=FakeBudgets,
            sts_factory=FakeSTS,
        ),
        ce,
    )


class FakeToken:
    token = "token"


class FakeCredential:
    def get_token(self, scope: str) -> FakeToken:
        return FakeToken()


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeAzureClient:
    def __init__(self, routes: dict[str, dict[str, Any]], calls: list[Any]) -> None:
        self.routes = routes
        self.calls = calls

    async def __aenter__(self) -> "FakeAzureClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        for suffix, payload in self.routes.items():
            if url.endswith(suffix):
                return FakeResponse(payload)
        raise AssertionError(url)


def azure(routes: dict[str, dict[str, Any]]) -> tuple[AzureInsightsProvider, list[Any]]:
    calls: list[Any] = []
    return (
        AzureInsightsProvider(
            subscription_id="sub",
            credential=FakeCredential(),
            client_factory=lambda **_: FakeAzureClient(routes, calls),
        ),
        calls,
    )


@pytest.mark.asyncio
async def test_aws_forecast_sums_prediction_interval() -> None:
    provider, ce = aws()
    result = await provider.forecast(date(2026, 11, 2), date(2026, 12, 1))
    assert result.amount == Decimal("120.50")
    assert (result.lower_bound, result.upper_bound) == (Decimal("100"), Decimal("140"))
    assert ce.calls[0][1]["Metric"] == "UNBLENDED_COST"


@pytest.mark.asyncio
async def test_aws_anomalies_paginate_and_keep_root_causes() -> None:
    provider, ce = aws()
    anomalies = await provider.anomalies(date(2026, 10, 1), date(2026, 11, 1))
    assert len([call for call in ce.calls if call[0] == "anomalies"]) == 2
    assert anomalies[0].impact == Decimal("42.5")
    assert anomalies[0].root_causes[0]["Region"] == "us-east-1"


@pytest.mark.asyncio
async def test_aws_budgets_and_tag_costs() -> None:
    provider, ce = aws()
    budgets = await provider.budgets()
    assert budgets[0].utilization == Decimal("85")
    assert budgets[0].forecast == Decimal("110")
    tags = await provider.cost_by_tag("team", date(2026, 10, 1), date(2026, 11, 1))
    assert {(tag.tag_value, tag.amount) for tag in tags} == {
        ("platform", Decimal("10")),
        ("(untagged)", Decimal("3")),
    }
    assert ce.calls[-1][1]["GroupBy"] == [{"Type": "TAG", "Key": "team"}]


def test_detect_anomalies_flags_spike_only() -> None:
    start = date(2026, 10, 1)
    daily = [(start + timedelta(days=i), Decimal("10") + Decimal(i % 2)) for i in range(20)]
    daily.append((start + timedelta(days=20), Decimal("90")))
    anomalies = detect_anomalies("azure", daily, "USD")
    assert [anomaly.start_date for anomaly in anomalies] == [start + timedelta(days=20)]
    assert anomalies[0].impact > Decimal("75")


@pytest.mark.asyncio
async def test_azure_forecast_budgets_tags_and_anomalies() -> None:
    days = [
        [10.0, int((date(2026, 9, 3) + timedelta(days=i)).strftime("%Y%m%d")), "EUR"]
        for i in range(58)
    ]
    days.append([200.0, 20261031, "EUR"])
    provider, calls = azure(
        {
            "/forecast": {
                "properties": {
                    "columns": [{"name": "Cost"}, {"name": "Currency"}],
                    "rows": [[5.5, "EUR"], [4.5, "EUR"]],
                }
            },
            "/budgets": {
                "value": [
                    {
                        "name": "team",
                        "properties": {
                            "amount": 50,
                            "currentSpend": {"amount": 60, "unit": "EUR"},
                            "timeGrain": "Monthly",
                        },
                    }
                ]
            },
        }
    )
    forecast = await provider.forecast(date(2026, 11, 2), date(2026, 12, 1))
    assert (forecast.amount, forecast.currency) == (Decimal("10.0"), "EUR")
    budgets = await provider.budgets()
    assert budgets[0].utilization == Decimal("120")

    provider.__dict__["_client_factory"] = lambda **_: FakeAzureClient(
        {
            "/query": {
                "properties": {
                    "columns": [
                        {"name": "PreTaxCost"},
                        {"name": "UsageDate"},
                        {"name": "Currency"},
                    ],
                    "rows": days,
                }
            }
        },
        calls,
    )
    anomalies = await provider.anomalies(date(2026, 10, 2), date(2026, 11, 1))
    assert [anomaly.start_date for anomaly in anomalies] == [date(2026, 10, 31)]
    assert anomalies[0].source == "statistical"

    provider.__dict__["_client_factory"] = lambda **_: FakeAzureClient(
        {
            "/query": {
                "properties": {
                    "columns": [
                        {"name": "PreTaxCost"},
                        {"name": "TagKey"},
                        {"name": "TagValue"},
                        {"name": "Currency"},
                    ],
                    "rows": [[7, "team", "data", "EUR"], [2, "team", None, "EUR"]],
                }
            }
        },
        calls,
    )
    tags = await provider.cost_by_tag("team", date(2026, 10, 1), date(2026, 11, 1))
    assert {tag.tag_value for tag in tags} == {"data", "(untagged)"}
    assert calls[-1][2]["json"]["dataset"]["grouping"] == [{"type": "TagKey", "name": "team"}]


@pytest.mark.asyncio
async def test_azure_requires_subscription() -> None:
    provider = AzureInsightsProvider(subscription_id="", credential=FakeCredential())
    provider.subscription_id = ""
    with pytest.raises(FinOpsQueryError):
        await provider.budgets()


class StubProvider:
    def __init__(self, name: str, fail: bool = False) -> None:
        self.name = name
        self.fail = fail

    def _check(self) -> None:
        if self.fail:
            raise FinOpsQueryError("boom")

    async def forecast(self, start: date, end: date) -> ForecastResult:
        self._check()
        return ForecastResult(
            provider_name=self.name,
            amount=Decimal("5"),
            currency="USD",
            start_date=start,
            end_date=end,
        )

    async def anomalies(self, start: date, end: date) -> list[CostAnomaly]:
        self._check()
        return [
            CostAnomaly(provider_name=self.name, source="x", start_date=start, impact=Decimal(2)),
            CostAnomaly(provider_name=self.name, source="x", start_date=start, impact=Decimal(20)),
        ]

    async def budgets(self) -> list[BudgetStatus]:
        self._check()
        return [
            BudgetStatus(
                provider_name=self.name,
                name="b",
                limit=Decimal(100),
                actual=Decimal(50),
                forecast=Decimal(120),
                currency="USD",
            )
        ]

    async def cost_by_tag(self, tag_key: str, start: date, end: date) -> list[TagCost]:
        self._check()
        return [
            TagCost(
                provider_name=self.name,
                tag_key=tag_key,
                tag_value="prod",
                amount=Decimal(9),
                currency="USD",
            )
        ]


def service() -> FinOpsInsightsService:
    return FinOpsInsightsService({"aws": StubProvider("aws"), "azure": StubProvider("azure", True)})


@pytest.mark.asyncio
async def test_tools_report_partial_results() -> None:
    forecast = await FinOpsForecastTool(service()).execute({})
    assert forecast["partial"] is True
    assert forecast["providers_failed"] == ["azure"]
    assert forecast["forecasts"][0]["amount"] == "5"

    anomalies = await FinOpsAnomaliesTool(service()).execute({"min_impact": 10})
    assert anomalies["count"] == 1

    budgets = await FinOpsBudgetsTool(service()).execute({"providers": ["aws"]})
    assert budgets["budgets"][0]["alert"] is True
    assert budgets["partial"] is False

    tags = await FinOpsCostByTagTool(service()).execute({"tag_key": "env"})
    assert tags["groups"][0]["tag_value"] == "prod"


@pytest.mark.asyncio
async def test_tools_validate_input() -> None:
    with pytest.raises(FinOpsQueryError):
        await FinOpsCostByTagTool(service()).execute({"tag_key": ""})
    with pytest.raises(FinOpsQueryError):
        await FinOpsForecastTool(service()).execute(
            {"start_date": "2020-01-01", "end_date": "2020-02-01"}
        )
    with pytest.raises(FinOpsQueryError):
        await FinOpsBudgetsTool(service()).execute({"providers": ["gcp"]})
