"""Shared deterministic provider resilience primitives."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeVar

from multicloud_mcp.domain.exceptions import ProviderUnavailableError, UpstreamProviderError

T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ProviderCircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    failures: int = field(default=0, init=False)
    last_failure: float = field(default=0.0, init=False)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)

    def can_execute(self) -> bool:
        if self.state is CircuitState.CLOSED:
            return True
        if (
            self.state is CircuitState.OPEN
            and time.monotonic() - self.last_failure >= self.recovery_timeout
        ):
            self.state = CircuitState.HALF_OPEN
            return True
        return self.state is CircuitState.HALF_OPEN

    def success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED

    def failure(self) -> None:
        self.failures += 1
        self.last_failure = time.monotonic()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN


class ResilientExecutor:
    """Apply timeout, bounded retries, circuit breaking, and concurrency limits."""

    def __init__(
        self,
        provider: str,
        timeout: float = 60.0,
        retries: int = 2,
        max_concurrency: int = 10,
        breaker: ProviderCircuitBreaker | None = None,
    ) -> None:
        self.provider = provider
        self.timeout = timeout
        self.retries = max(0, retries)
        self.semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self.breaker = breaker or ProviderCircuitBreaker()

    async def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        if not self.breaker.can_execute():
            raise ProviderUnavailableError(f"Provider circuit is open: {self.provider}")
        async with self.semaphore:
            for attempt in range(self.retries + 1):
                try:
                    result = await asyncio.wait_for(operation(), timeout=self.timeout)
                    self.breaker.success()
                    return result
                except (TimeoutError, ConnectionError) as exc:
                    self.breaker.failure()
                    if attempt >= self.retries:
                        raise UpstreamProviderError(
                            f"Provider operation failed: {self.provider}"
                        ) from exc
                    await asyncio.sleep(min(0.25 * (attempt + 1), 1.0))
                except Exception as exc:
                    self.breaker.failure()
                    raise UpstreamProviderError(
                        f"Provider operation failed: {self.provider}"
                    ) from exc
        raise UpstreamProviderError(f"Provider operation failed: {self.provider}")
