# Operations

## Endpoints
`POST /mcp`, `GET /health`, `GET /metrics`.

## Health
Provider failures can degrade service without necessarily taking down the entire gateway.

## Metrics
Prometheus-style metrics should avoid high-cardinality/sensitive labels such as request ID, client IP, account ID, subscription ID, or resource ID.

## Logging
Structured `structlog` events cover provider lifecycle, tool errors, policy rejections, and audit context.

## Rate limiting
The built-in limiter is intended for single-instance deployments. Use a gateway/reverse proxy/distributed limiter for multi-instance deployments.

## Troubleshooting
Check `/health`, provider initialization logs, cloud credentials/permissions, namespaces, policy rejections, auth/rate-limit failures, and whether the requested provider-native tool was discovered.
