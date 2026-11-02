"""Tool-call metrics in Prometheus text format and optional OpenTelemetry tracing."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterator
from typing import Any

import structlog

logger = structlog.get_logger()

LATENCY_BUCKETS_MS = (25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000)


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class ToolMetrics:
    """Per-tool call counters and latency histograms without external dependencies."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._calls: dict[tuple[str, str], int] = {}
        self._buckets: dict[str, list[int]] = {}
        self._sum_ms: dict[str, float] = {}
        self._count: dict[str, int] = {}

    def observe(self, tool: str, outcome: str, duration_ms: float) -> None:
        with self._lock:
            self._calls[(tool, outcome)] = self._calls.get((tool, outcome), 0) + 1
            buckets = self._buckets.setdefault(tool, [0] * len(LATENCY_BUCKETS_MS))
            for index, bound in enumerate(LATENCY_BUCKETS_MS):
                if duration_ms <= bound:
                    buckets[index] += 1
            self._sum_ms[tool] = self._sum_ms.get(tool, 0.0) + duration_ms
            self._count[tool] = self._count.get(tool, 0) + 1

    def render(self) -> list[str]:
        with self._lock:
            lines = [
                "# HELP multicloud_tool_executions_total Tool executions by tool and outcome",
                "# TYPE multicloud_tool_executions_total counter",
            ]
            for (tool, outcome), value in sorted(self._calls.items()):
                lines.append(
                    f'multicloud_tool_executions_total{{tool="{_label(tool)}",'
                    f'outcome="{_label(outcome)}"}} {value}'
                )
            lines += [
                "# HELP multicloud_tool_duration_ms Tool execution latency in milliseconds",
                "# TYPE multicloud_tool_duration_ms histogram",
            ]
            for tool, buckets in sorted(self._buckets.items()):
                name = _label(tool)
                for bound, value in zip(LATENCY_BUCKETS_MS, buckets, strict=True):
                    lines.append(
                        f'multicloud_tool_duration_ms_bucket{{tool="{name}",le="{bound}"}} {value}'
                    )
                lines.append(
                    f'multicloud_tool_duration_ms_bucket{{tool="{name}",le="+Inf"}} {self._count[tool]}'
                )
                lines.append(
                    f'multicloud_tool_duration_ms_sum{{tool="{name}"}} {self._sum_ms[tool]:.3f}'
                )
                lines.append(
                    f'multicloud_tool_duration_ms_count{{tool="{name}"}} {self._count[tool]}'
                )
            return lines


class Tracer:
    """Thin wrapper that is a no-op unless OpenTelemetry is installed and enabled."""

    def __init__(self, enabled: bool = False, service_name: str = "multicloud-mcp-server") -> None:
        self._tracer: Any = None
        if not enabled:
            return
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
        except ImportError:
            logger.warning(
                "tracing_unavailable",
                reason="install the 'otel' extra: pip install multicloud-mcp-server[otel]",
            )
            return
        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer("multicloud_mcp")

    @property
    def enabled(self) -> bool:
        return self._tracer is not None

    @contextlib.contextmanager
    def span(self, name: str, **attributes: str | None) -> Iterator[Any]:
        if self._tracer is None:
            yield None
            return
        with self._tracer.start_as_current_span(name) as span:
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(f"mcp.{key}", value)
            yield span
