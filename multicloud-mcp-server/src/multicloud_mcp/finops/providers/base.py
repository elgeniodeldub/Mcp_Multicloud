"""Provider interface for the FinOps bounded context."""

from typing import Protocol

from multicloud_mcp.finops.models import FinOpsCostResult, FinOpsQuery


class FinOpsProvider(Protocol):
    """Common async contract implemented by AWS and Azure adapters."""

    name: str

    async def query_cost(self, query: FinOpsQuery) -> list[FinOpsCostResult]:
        """Execute one aggregated live cost query."""
