"""Per-client rate limiters: bounded in-memory (one instance) or Redis (shared)."""

from __future__ import annotations

import time
from collections import OrderedDict, deque
from collections.abc import Awaitable
from typing import Any, Protocol


class RateLimitExceededError(Exception):
    """Raised when a client exceeds its request budget."""


class RateLimiter(Protocol):
    """A limiter's check may be sync (in-memory) or async (Redis)."""

    def check(self, client_key: str) -> None | Awaitable[None]: ...


class InMemoryRateLimiter:
    """Sliding-window limiter with bounded client state for single instances."""

    def __init__(self, requests_per_minute: int, max_clients: int = 10_000) -> None:
        if requests_per_minute < 1:
            raise ValueError("security.rate_limit.requests_per_minute must be at least 1")
        self.limit = requests_per_minute
        self.max_clients = max_clients
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()

    def check(self, client_key: str) -> None:
        now = time.monotonic()
        timestamps = self._requests.get(client_key)
        if timestamps is None:
            if len(self._requests) >= self.max_clients:
                self._requests.popitem(last=False)
            timestamps = deque()
            self._requests[client_key] = timestamps
        else:
            self._requests.move_to_end(client_key)

        while timestamps and timestamps[0] <= now - 60:
            timestamps.popleft()
        if len(timestamps) >= self.limit:
            raise RateLimitExceededError
        timestamps.append(now)


class RedisRateLimiter:
    """Fixed one-minute window shared by all replicas through Redis.

    Fails open when Redis is unreachable so a cache outage does not take the API
    down; the in-process limiter is used as a fallback in that case.
    """

    def __init__(
        self,
        client: Any,
        requests_per_minute: int,
        prefix: str = "multicloud-mcp:ratelimit",
    ) -> None:
        if requests_per_minute < 1:
            raise ValueError("security.rate_limit.requests_per_minute must be at least 1")
        self.client = client
        self.limit = requests_per_minute
        self.prefix = prefix
        self._fallback = InMemoryRateLimiter(requests_per_minute)

    @classmethod
    def from_url(cls, url: str, requests_per_minute: int) -> RedisRateLimiter:
        import redis.asyncio as redis

        return cls(redis.from_url(url, socket_timeout=0.5), requests_per_minute)

    async def check(self, client_key: str) -> None:
        window = int(time.time() // 60)
        key = f"{self.prefix}:{client_key}:{window}"
        try:
            pipeline = self.client.pipeline(transaction=True)
            pipeline.incr(key)
            pipeline.expire(key, 61)
            count, _ = await pipeline.execute()
        except Exception:
            self._fallback.check(client_key)
            return
        if int(count) > self.limit:
            raise RateLimitExceededError
