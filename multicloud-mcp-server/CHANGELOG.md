# Changelog

## [Unreleased] - 2026-08-11

### Added
- Live FinOps queries for AWS Cost Explorer and Azure Cost Management.
- GCP public Cloud Billing Catalog list-price lookup through
  `finops__gcp_list_prices`.
- Canonical multicloud domain models, capability contracts, provider/tool
  registries, and a shared application execution layer.
- HTTP security controls: Bearer authentication, restrictive CORS, request
  limits, rate limiting, request IDs, audit logging, and read-only policy.
- Hermes Agent integration examples and external MCP validation fixtures.
- Cloud installation manuals for AWS, Azure, and GCP.

### Changed
- Native tools now use standardized metadata, safety classifications,
  execution context, result envelopes, and normalized application errors.
- Provider transport, retry, timeout, circuit-breaker, and concurrency
  behavior is shared between provider adapters.
- AWS raw MCP passthrough is disabled by default until a compatible upstream
  package is validated.
- Azure MCP passthrough is pinned to `@azure/mcp@2.0.4` with `server start`
  for Windows stability and correct stdio startup.
- HTTP binds to `127.0.0.1` by default.

### Security
- Added supply-chain and CI hardening documentation, dependency and secret
  scanning configuration, Docker scanning, and release verification guidance.
- Credentials remain environment/configuration-local only and are excluded
  from repository documentation and examples.

### Documentation
- Documented that GCP support is limited to public list prices and does not
  provide actual GCP billing, BigQuery exports, or a full GCP provider.

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
