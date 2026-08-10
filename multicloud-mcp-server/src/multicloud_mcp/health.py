"""Health monitoring and circuit breaker for upstream providers."""

from __future__ import annotations

import asyncio
import time
from contextlib import suppress
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for a single provider."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

    failures: int = field(default=0, init=False)
    last_failure_time: float = field(default=0.0, init=False)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    half_open_calls: int = field(default=0, init=False)

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self._close()
        else:
            self.failures = max(0, self.failures - 1)

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN or self.failures >= self.failure_threshold:
            self._open()

    def can_execute(self) -> bool:
        """Check if a call should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._half_open()
                return True
            return False
        return self.half_open_calls < self.half_open_max_calls

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self.half_open_calls = 0
        logger.warning("circuit_breaker_opened")

    def _half_open(self) -> None:
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        logger.info("circuit_breaker_half_open")

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.half_open_calls = 0
        logger.info("circuit_breaker_closed")


class HealthMonitor:
    """Monitors health of all registered providers."""

    def __init__(self, check_interval: float = 30.0) -> None:
        self.check_interval = check_interval
        self._breakers: dict[str, CircuitBreaker] = {}
        self._providers: dict[str, ProviderAdapter] = {}
        self._task: asyncio.Task[Any] | None = None
        self._stop_event = asyncio.Event()
        self._logger = logger.bind(component="health_monitor")

    def register_provider(self, name: str, provider: ProviderAdapter) -> None:
        """Register a provider for monitoring."""
        self._providers[name] = provider
        self._breakers[name] = CircuitBreaker()

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider."""
        self._providers.pop(name, None)
        self._breakers.pop(name, None)

    def is_provider_available(self, name: str) -> bool:
        """Check if provider is available (circuit closed)."""
        breaker = self._breakers.get(name)
        return breaker.can_execute() if breaker else False

    def record_result(self, name: str, success: bool) -> None:
        """Record call result for circuit breaker."""
        breaker = self._breakers.get(name)
        if breaker:
            if success:
                breaker.record_success()
            else:
                breaker.record_failure()

    async def start(self) -> None:
        """Start periodic health checks."""
        self._task = asyncio.create_task(self._monitor_loop())
        self._logger.info("health_monitor_started", interval=self.check_interval)

    async def stop(self) -> None:
        """Stop health monitoring."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        self._logger.info("health_monitor_stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.check_interval,
                )
            except TimeoutError:
                await self._check_all()

    async def _check_all(self) -> None:
        """Check all providers."""
        tasks = []
        names = []
        for name, provider in self._providers.items():
            if not self._breakers[name].can_execute():
                continue
            tasks.append(self._check_provider(name, provider))
            names.append(name)
        if not tasks:
            return
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(names, results, strict=True):
            if isinstance(result, BaseException):
                self._breakers[name].record_failure()
                self._logger.warning("health_check_failed", provider=name, error=str(result))
            else:
                health: ProviderHealth = result
                if health.healthy:
                    self._breakers[name].record_success()
                else:
                    self._breakers[name].record_failure()
                self._logger.debug(
                    "health_check_result",
                    provider=name,
                    healthy=health.healthy,
                    latency_ms=health.latency_ms,
                )

    async def _check_provider(self, name: str, provider: ProviderAdapter) -> ProviderHealth:
        """Check a single provider."""
        return await provider.health_check()
