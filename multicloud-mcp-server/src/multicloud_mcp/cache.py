"""In-memory cache for tools catalog with TTL support."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Generic, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with TTL."""

    value: T
    created_at: float = field(default_factory=time.time)
    ttl: float = 300.0

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl


class ToolsCache:
    """Cache for provider tools catalog."""

    def __init__(self, default_ttl: float = 300.0) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._logger = logger.bind(component="tools_cache")

    def get(self, key: str):
        """Get cached tools if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            self._logger.debug("cache_entry_expired", key=key)
            del self._cache[key]
            return None
        self._logger.debug("cache_hit", key=key)
        return entry.value

    def set(self, key: str, value, ttl: float | None = None) -> None:
        """Store tools in cache."""
        self._cache[key] = CacheEntry(
            value=value,
            ttl=ttl or self._default_ttl,
        )
        self._logger.debug("cache_set", key=key)

    def invalidate(self, key: str | None = None) -> None:
        """Invalidate cache entries."""
        if key is None:
            self._cache.clear()
            self._logger.info("cache_invalidated_all")
        else:
            self._cache.pop(key, None)
            self._logger.info("cache_invalidated", key=key)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = len(self._cache)
        expired = sum(1 for e in self._cache.values() if e.is_expired)
        return {
            "total_entries": total,
            "expired_entries": expired,
            "valid_entries": total - expired,
        }
