# Changelog

## [0.1.0] - 2024-XX-XX

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
