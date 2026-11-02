# Changelog

## [0.2.0] - 2026-11-02

### Added
- FinOps tools: `finops__forecast`, `finops__anomalies`, `finops__budgets`, `finops__cost_by_tag` for AWS and Azure.
- OAuth 2.1 / OIDC JWT authentication with per-tool scopes (`security.authentication.type: oidc`).
- Trusted reverse proxies (`security.trusted_proxies`), optional HSTS, Content-Security-Policy header.
- Redis backends for rate limiting and the FinOps cache (`redis` extra), both failing open.
- Per-tool execution counters and latency histograms on `/metrics`; optional OpenTelemetry tracing (`otel` extra).
- Container image preinstalls the pinned Azure MCP server; default container config at `/etc/multicloud-mcp/config.yaml`.
- CI smoke test of the pinned and latest Azure MCP releases on Linux and Windows.
- Release images pushed to GHCR, signed with cosign, with a signed SBOM attestation.
- Least-privilege IAM/RBAC guide.

### Changed
- `read_only` tool policy is now default-deny for provider passthrough tools: they need an allowlist entry or an upstream `readOnlyHint`, and command-like arguments are checked for mutating verbs.
- HTTP refuses to bind a non-loopback address without authentication unless `security.allow_unauthenticated_remote` is set.
- Rate limiting is keyed by authenticated subject when available.
- Package version is the single source for the server version.

## [0.1.0] - 2026-08-10

### Added
- Initial release of Multicloud MCP Server
- Support for AWS MCP Server (awslabs/mcp) via stdio
- Support for Azure MCP Server (microsoft/mcp) via stdio
- Namespace-based tool routing (`aws__*`, `azure__*`)
- Circuit breaker pattern for provider resilience
- Health monitoring with periodic checks
- Tools cache with TTL
- Native multicloud tools:
  - `multicloud__compare_cost`
  - `multicloud__map_resource`
  - `multicloud__list_providers`
  - `multicloud__discover_resources`
  - `multicloud__security_posture`
  - `multicloud__compliance_check`
- Configuration via YAML and environment variables
- stdio and HTTP transport support
- Docker support
- CI/CD with GitHub Actions
