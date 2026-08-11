"""Request-scoped execution context passed through application services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExecutionContext:
    """Safe request metadata; credentials and authorization headers are excluded."""

    request_id: str
    providers: tuple[str, ...] = ()
    timeout_seconds: float | None = None
    region: str | None = None
    account: str | None = None
    transport: str = "stdio"
    caller: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_arguments(
        cls,
        request_id: str,
        arguments: dict[str, Any],
        transport: str,
        timeout_seconds: float | None = None,
    ) -> ExecutionContext:
        """Build context from safe, tool-independent request fields."""
        providers_value = arguments.get("providers", ())
        providers = tuple(str(value) for value in providers_value) if isinstance(providers_value, list) else ()
        metadata = arguments.get("metadata", {})
        safe_metadata = {
            str(key): str(value)
            for key, value in metadata.items()
            if isinstance(metadata, dict) and str(key).lower() not in {"token", "secret", "password", "authorization"}
        }
        return cls(
            request_id=request_id,
            providers=providers,
            timeout_seconds=timeout_seconds,
            region=str(arguments["region"]) if arguments.get("region") else None,
            account=str(arguments["account"]) if arguments.get("account") else None,
            transport=transport,
            metadata=safe_metadata,
        )
