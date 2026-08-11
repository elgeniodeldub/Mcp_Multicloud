"""Stable application result and error envelopes for agent-facing tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApplicationError:
    """Safe, stable error information intended for an MCP client."""

    code: str
    message: str
    provider: str | None = None


@dataclass
class ToolExecutionResult:
    """Common result envelope while preserving native tool data unchanged."""

    data: Any = None
    errors: list[ApplicationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    partial: bool = False
    providers: list[str] = field(default_factory=list)
    request_id: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the envelope without exposing exception internals."""
        value = asdict(self)
        value["errors"] = [asdict(error) for error in self.errors]
        return value

    def legacy_data(self) -> Any:
        """Return the original tool payload for backward-compatible MCP responses."""
        if not self.errors:
            return self.data
        return {
            "error": self.errors[0].code,
            "message": self.errors[0].message,
            "partial": self.partial,
            "providers": self.providers,
        }
