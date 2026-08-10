"""Provider registry and configuration-driven provider factory."""

from __future__ import annotations

from collections.abc import Callable

from multicloud_mcp.config import ProviderConfig
from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider
from multicloud_mcp.providers.base import ProviderAdapter


class ProviderRegistryError(Exception):
    """Base error for provider registry operations."""


class DuplicateProviderError(ProviderRegistryError):
    """Raised when a provider name is registered twice."""


class UnknownProviderError(ProviderRegistryError):
    """Raised when no factory exists for a configured provider."""


class DisabledProviderError(ProviderRegistryError):
    """Raised when creation is requested for a disabled provider."""


ProviderFactory = Callable[[ProviderConfig], ProviderAdapter]


class ProviderRegistry:
    """Registry of provider factories, ready for future cloud adapters."""

    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}

    def register(self, name: str, factory: ProviderFactory) -> None:
        """Register a provider factory and reject duplicates."""
        normalized = name.lower()
        if normalized in self._factories:
            raise DuplicateProviderError(f"Provider already registered: {name}")
        self._factories[normalized] = factory

    def create(self, name: str, config: ProviderConfig) -> ProviderAdapter:
        """Create an enabled provider from configuration."""
        normalized = name.lower()
        if not config.enabled:
            raise DisabledProviderError(f"Provider is disabled: {name}")
        factory = self._factories.get(normalized)
        if factory is None:
            raise UnknownProviderError(f"Unknown provider: {name}")
        return factory(config)

    def supports(self, name: str) -> bool:
        """Return whether a provider factory is registered."""
        return name.lower() in self._factories

    def list_providers(self) -> list[str]:
        """List registered provider names."""
        return list(self._factories)


def build_provider_registry() -> ProviderRegistry:
    """Build the default AWS/Azure provider registry."""
    registry = ProviderRegistry()
    registry.register(
        "aws",
        lambda config: AWSProvider(
            command=config.command,
            args=config.args,
            env=config.env,
            timeout=config.timeout,
            max_concurrency=config.max_concurrency,
            retry_attempts=config.retry_attempts,
            circuit_failure_threshold=config.circuit_failure_threshold,
            circuit_recovery_timeout=config.circuit_recovery_timeout,
        ),
    )
    registry.register(
        "azure",
        lambda config: AzureProvider(
            command=config.command,
            args=config.args,
            env=config.env,
            timeout=config.timeout,
            max_concurrency=config.max_concurrency,
            retry_attempts=config.retry_attempts,
            circuit_failure_threshold=config.circuit_failure_threshold,
            circuit_recovery_timeout=config.circuit_recovery_timeout,
        ),
    )
    return registry
