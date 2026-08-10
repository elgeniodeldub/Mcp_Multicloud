"""Application/domain exceptions shared by multicloud services."""

from __future__ import annotations


class DomainError(Exception):
    """Base error for provider-independent application operations."""


class ProviderUnavailableError(DomainError):
    """A provider cannot currently serve the requested operation."""


class CapabilityNotSupportedError(DomainError):
    """A provider does not expose a requested semantic capability."""


class InvalidQueryError(DomainError):
    """The application query is invalid."""


class AuthenticationError(DomainError):
    """Provider authentication failed."""


class RateLimitError(DomainError):
    """An upstream provider rate limited a request."""


class UpstreamProviderError(DomainError):
    """A normalized error from a provider transport or SDK."""
