"""Tests for canonical domain models, capabilities, and resilience."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from multicloud_mcp.domain.mappers import (
    cost_record_from_finops,
    normalize_severity,
    normalize_state,
    resource_from_mapping,
)
from multicloud_mcp.domain.models import CloudProvider, CostReport, Severity
from multicloud_mcp.finops.models import FinOpsCostResult
from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider
from multicloud_mcp.providers.capabilities import Capability
from multicloud_mcp.providers.resilience import (
    CircuitState,
    ProviderCircuitBreaker,
    ResilientExecutor,
)


def test_canonical_resource_mapping_and_normalization() -> None:
    aws = resource_from_mapping(
        "aws",
        {
            "arn": "arn:aws:ec2:us-east-1:123:instance/i-1",
            "name": "web",
            "type": "instance",
            "region": "us-east-1",
            "state": "running",
            "tags": {"env": "prod"},
        },
    )
    azure = resource_from_mapping(
        "azure",
        {"resourceId": "/subscriptions/s/resourceGroups/r/providers/x", "location": "eastus"},
    )
    assert aws.provider is CloudProvider.AWS
    assert aws.state.value == "running"
    assert aws.tags == {"env": "prod"}
    assert azure.provider is CloudProvider.AZURE
    assert azure.region == "eastus"
    assert normalize_state("deallocated").value == "stopped"
    assert normalize_severity("HIGH") is Severity.HIGH
    assert normalize_severity("not-a-severity") is Severity.UNKNOWN


def test_cost_domain_preserves_decimal_precision_and_currencies() -> None:
    first = FinOpsCostResult(
        provider_name="aws",
        sub_account_id="123",
        service_name="Amazon EC2",
        service_category=None,
        region_id="us-east-1",
        billed_cost=None,
        effective_cost=Decimal("0.1000000001"),
        currency="USD",
        start_date=date(2026, 5, 1),
        end_date=date(2026, 6, 1),
    )
    record = cost_record_from_finops(first)
    report = CostReport.from_records([record, record.model_copy(update={"currency": "EUR"})])
    assert record.amount == Decimal("0.1000000001")
    assert report.totals_by_currency == {
        "USD": Decimal("0.1000000001"),
        "EUR": Decimal("0.1000000001"),
    }
    assert "provider" in record.model_dump_json()


def test_aws_and_azure_declare_semantic_capabilities() -> None:
    aws = AWSProvider()
    azure = AzureProvider()
    assert aws.supports(Capability.COMPUTE)
    assert aws.supports(Capability.KUBERNETES)
    assert azure.supports(Capability.STORAGE)
    assert not azure.supports(Capability.COST)


class FakeTransport:
    def __init__(self) -> None:
        self.connected = False

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def list_tools(self) -> SimpleNamespace:
        return SimpleNamespace(
            tools=[
                SimpleNamespace(
                    name="ec2__describe_instances", description="compute", inputSchema={}
                )
            ]
        )

    async def call_tool(self, name: str, arguments: dict[str, object]) -> SimpleNamespace:
        return SimpleNamespace(content=[], isError=False)


@pytest.mark.asyncio
async def test_mcp_provider_transport_and_capability_execution() -> None:
    transport = FakeTransport()
    provider = AWSProvider(transport=transport)
    await provider.connect()
    result = await provider.execute_capability(Capability.COMPUTE, {})
    assert transport.connected
    assert result["isError"] is False
    await provider.disconnect()
    assert not transport.connected


@pytest.mark.asyncio
async def test_resilience_retries_transient_and_limits_concurrency() -> None:
    executor = ResilientExecutor("test", timeout=1, retries=1, max_concurrency=1)
    attempts = 0

    async def transient() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError
        return "ok"

    assert await executor.run(transient) == "ok"
    assert attempts == 2

    active = 0
    peak = 0

    async def limited() -> None:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1

    await asyncio.gather(*(executor.run(limited) for _ in range(3)))
    assert peak == 1


def test_circuit_breaker_open_and_recovery() -> None:
    breaker = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=0)
    breaker.failure()
    breaker.failure()
    assert breaker.state is CircuitState.OPEN
    assert breaker.can_execute()
    breaker.success()
    assert breaker.state is CircuitState.CLOSED
