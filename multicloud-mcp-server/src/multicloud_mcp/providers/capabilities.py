"""Semantic provider capabilities, independent of upstream tool names."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol


class Capability(StrEnum):
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    KUBERNETES = "kubernetes"
    COST = "cost"
    SECURITY = "security"


class CapabilityProvider(Protocol):
    """Contract exposed by providers to application-level multicloud logic."""

    name: str

    def supports(self, capability: Capability) -> bool:
        """Return whether the provider supports a capability."""
        ...

    async def execute_capability(
        self, capability: Capability, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a semantic capability and return normalized application data."""
        ...
