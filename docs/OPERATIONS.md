# Operations

## Endpoints
`POST /mcp`, `GET /health`, `GET /metrics`.

## Health
Provider failures can degrade service without necessarily taking down the entire gateway.

## Metrics
`GET /metrics` serves Prometheus text format: HTTP counters plus `multicloud_tool_executions_total{tool,outcome}` and the latency histogram `multicloud_tool_duration_ms{tool}`. Labels are limited to tool name and outcome; never add request ID, client IP, account, subscription, or resource IDs.

## Tracing
Install the `otel` extra (`pip install "multicloud-mcp-server[otel]"`) and set `observability.tracing_enabled: true`. Each tool call becomes an `mcp.tool_call` span with tool, transport, request ID, caller, and outcome attributes. The exporter is OTLP/HTTP configured through the standard `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` variables.

## Logging
Structured `structlog` events cover provider lifecycle, tool errors, policy rejections, and audit context.

## Scaling out (Redis)
The default in-memory rate limiter and FinOps cache are per process. With several replicas, install the `redis` extra and set:

```yaml
security:
  rate_limit:
    backend: redis
    redis_url_env: MULTICLOUD_REDIS_URL
cache:
  backend: redis
  redis_url_env: MULTICLOUD_REDIS_URL
  ttl_seconds: 300
```

`MULTICLOUD_REDIS_URL` (for example `rediss://:password@redis:6380/0`) comes from the environment. Both backends fail open: if Redis is unreachable, rate limiting falls back to the in-process limiter and the cache to a miss, so Redis is never a single point of failure. Cached values are JSON, never pickle, and partial (provider-failure) results are not shared.

## Azure MCP version pin
CI runs `scripts/azure_mcp_smoke.py` on Linux and Windows against the pinned `@azure/mcp` version and against `latest`. The `latest` leg is informational; when it passes on Windows, raise the pin in `config.yaml` and `AZURE_MCP_VERSION` in the Dockerfile together. Run it locally with `python scripts/azure_mcp_smoke.py --version <x.y.z>`.

## Troubleshooting
Check `/health`, provider initialization logs, cloud credentials/permissions, namespaces, policy rejections, auth/rate-limit failures, and whether the requested provider-native tool was discovered.
