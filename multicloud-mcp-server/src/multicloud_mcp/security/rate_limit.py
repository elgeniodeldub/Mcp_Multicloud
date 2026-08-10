"""Bounded in-memory per-client rate limiter."""

from __future__ import annotations

import time
from collections import OrderedDict, deque


class RateLimitExceededError(Exception):
    """Raised when a client exceeds its request budget."""


class InMemoryRateLimiter:
    """Sliding-window limiter with bounded client state for single instances."""

    def __init__(self, requests_per_minute: int, max_clients: int = 10_000) -> None:
        if requests_per_minute < 1:
            raise ValueError("security.rate_limit.requests_per_minute must be at least 1")
        self.limit = requests_per_minute
        self.max_clients = max_clients
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()

    def check(self, client_ip: str) -> None:
        now = time.monotonic()
        timestamps = self._requests.get(client_ip)
        if timestamps is None:
            if len(self._requests) >= self.max_clients:
                self._requests.popitem(last=False)
            timestamps = deque()
            self._requests[client_ip] = timestamps
        else:
            self._requests.move_to_end(client_ip)

        while timestamps and timestamps[0] <= now - 60:
            timestamps.popleft()
        if len(timestamps) >= self.limit:
            raise RateLimitExceededError
        timestamps.append(now)
