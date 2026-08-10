# Features

## Provider support

### AWS

AWS is implemented as a provider adapter and participates in provider tool discovery, invocation, and health monitoring.

### Azure

Azure is implemented through the same provider abstraction and can coexist with AWS in the same MCP server instance.

## Dynamic tool discovery

The provider router asks each configured provider for its available tools and combines them into a single index.

Benefits:

- new provider tools can become available without hard-coding each tool in the core server;
- provider tools remain isolated by namespace;
- failed provider discovery can be handled independently.

## Native multicloud capabilities

### Provider inventory

`ListProvidersTool` provides visibility into the providers connected to the multicloud layer.

### Resource discovery

`DiscoverResourcesTool` provides a provider-agnostic entry point for finding cloud resources.

### Resource mapping

`ResourceMapperTool` maps provider-specific resource representations into a normalized multicloud model.

This is a foundational capability for cross-cloud inventory, FinOps, governance, security, and reporting.

### Cost comparison

`CostComparisonTool` is the cross-cloud cost comparison layer. A confirmed MCP name handled by the server is:

```text
multicloud__compare_cost
```

The tool should be treated as a multicloud orchestration feature rather than a replacement for provider billing APIs.

### Security posture

`SecurityPostureTool` aggregates security-oriented information from provider capabilities into a multicloud response.

### Compliance

`ComplianceCheckerTool` provides compliance-oriented checks/reporting across providers.

## Provider health monitoring

The server includes provider health checks and circuit-breaker behavior.

Advantages:

- fail fast when a provider is known to be unavailable;
- avoid repeated expensive/slow calls to a failing integration;
- prevent one provider outage from cascading to the complete server.

## Structured logging

`structlog` is used for structured operational events. This makes logs easier to consume from terminals, containers, or centralized logging platforms.

## HTTP and stdio support

### stdio

Best suited for:

- local MCP clients;
- desktop/CLI agents;
- process-managed integrations.

### HTTP

Best suited for:

- container deployments;
- service-to-service integration;
- remote MCP access where supported by the client architecture.

The HTTP implementation uses Starlette and Uvicorn.

## Configuration

Configuration supports YAML and environment-variable resolution. The server can load the default settings or an explicitly provided config path.

## Testing

The repository includes:

- provider adapter tests;
- native multicloud tool tests;
- end-to-end integration tests using mocked providers.

## Development quality gates

The repository is configured to use:

- `pytest`;
- `pytest-cov`;
- `mypy --strict`;
- `ruff`;
- pre-commit;
- CI workflow under `.github/workflows/`.
