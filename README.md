# Multicloud MCP Server

A Python-based **Model Context Protocol (MCP) server** that exposes a unified interface for working with multiple cloud providers.

The project currently integrates **AWS** and **Azure** through provider adapters and adds native multicloud capabilities for resource discovery, provider visibility, security posture, compliance, resource normalization, and cost comparison.

> Status: active development.

## Why this project exists

Cloud providers expose different APIs, naming conventions, resource models, and operational tooling. Multicloud MCP provides a single MCP-facing layer that can:

- connect to multiple cloud-specific providers;
- discover and route provider tools dynamically;
- expose cloud-specific tools without changing their original provider behavior;
- add normalized multicloud tools on top of the provider layer;
- isolate provider failures with health checks and circuit-breaker behavior;
- support both local MCP clients and HTTP-based integrations.

The goal is **not to duplicate every AWS or Azure API**. Provider-specific MCPs/APIs remain the adapters, while this project provides orchestration, normalization, and cross-cloud capabilities.

## Current providers

| Provider | Status | Adapter |
|---|---|---|
| AWS | Supported | `providers/aws.py` |
| Azure | Supported | `providers/azure.py` |
| GCP | Planned | Future adapter |

## Main features

### Unified provider routing

`ProviderRouter` discovers tools from configured providers and builds a single tool index. Provider-native tools can be exposed through provider namespaces while multicloud-native tools are handled directly by the server.

### Native multicloud tools

The repository currently contains six native tool implementations:

| Tool class | Purpose |
|---|---|
| `ListProvidersTool` | Lists configured providers and their availability/health context. |
| `DiscoverResourcesTool` | Discovers resources across supported providers. |
| `SecurityPostureTool` | Aggregates security posture information across providers. |
| `ComplianceCheckerTool` | Performs multicloud compliance-oriented checks/reporting. |
| `ResourceMapperTool` | Maps provider-specific resources into a common representation. |
| `CostComparisonTool` | Compares normalized cost/resource information across clouds. |

One confirmed MCP tool name is `multicloud__compare_cost`. The server registers the native tool definitions centrally in `server.py`.

See [docs/TOOLS.md](docs/TOOLS.md).

### AWS and Azure adapters

AWS and Azure are implemented behind a common provider abstraction. Adapters support operations such as:

- provider initialization;
- tool discovery;
- provider tool invocation;
- health checking;
- timeout/error isolation.

This design allows additional providers to be introduced without coupling the MCP server directly to cloud SDK details.

### Health monitoring and circuit breaking

`health.py` provides provider health monitoring and circuit-breaker behavior. A failing provider can be isolated instead of taking down the complete MCP server.

### Cache layer

`cache.py` provides a cache abstraction used by the server-side architecture to reduce unnecessary repeated provider operations.

### Configuration management

Configuration is implemented with Pydantic models/settings and supports YAML-based configuration plus environment-variable resolution.

A configuration file can be selected with:

```text
MULTICLOUD_CONFIG_PATH
```

The CLI also supports passing a config path explicitly.

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

### Structured logging

The project uses `structlog`, providing structured events suitable for local troubleshooting and centralized log processing.

### Multiple transports

The MCP server supports:

- **stdio** — for local MCP clients and agent integrations;
- **HTTP** — built with Starlette/Uvicorn for network-accessible deployments.

## Architecture

```text
                      MCP Client / Agent
                              |
                 +------------+------------+
                 |                         |
               stdio                      HTTP
                 |                         |
                 +------------+------------+
                              |
                    MulticloudMCPServer
                         server.py
                              |
              +---------------+---------------+
              |                               |
      Native Multicloud Tools          ProviderRouter
              |                               |
    +---------+---------+              +------+------+
    |         |         |              |             |
 Discover  Security  Compliance      AWS Adapter   Azure Adapter
 Resources  Posture    etc.             |             |
                                          Provider-specific
                                           MCP/API tools
```

The native tool layer is responsible for multicloud orchestration. Provider-specific behavior stays inside provider adapters.

For the detailed design, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository layout

```text
multicloud-mcp-server/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .pre-commit-config.yaml
├── Dockerfile
├── LICENSE
├── Makefile
├── pyproject.toml
├── README.md
├── src/
│   └── multicloud_mcp/
│       ├── __init__.py
│       ├── cache.py
│       ├── config.py
│       ├── health.py
│       ├── logging_config.py
│       ├── router.py
│       ├── server.py
│       ├── providers/
│       │   ├── base.py
│       │   ├── aws.py
│       │   └── azure.py
│       └── tools/
│           ├── cost_comparison.py
│           ├── discover_resources.py
│           ├── list_providers.py
│           ├── resource_mapper.py
│           ├── security_posture.py
│           └── compliance.py
└── tests/
    ├── integration/
    │   └── test_end_to_end.py
    ├── test_multicloud_tools.py
    └── test_providers.py
```

## Requirements

- Python 3
- access to the provider-specific MCP/API integrations configured by the project;
- valid AWS/Azure credentials where required by those integrations.

Use the project's `pyproject.toml` as the source of truth for the exact supported Python version and runtime dependencies.

## Local development setup

### Windows / PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Install development tooling if it is not already installed through project extras:

```powershell
python -m pip install pytest pytest-cov mypy ruff
```

### Linux / WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Running the server

Always check the current CLI options first:

```bash
python -m multicloud_mcp.server --help
```

Typical execution modes are:

```bash
python -m multicloud_mcp.server --transport stdio
```

or:

```bash
python -m multicloud_mcp.server --transport http
```

To load a specific configuration file:

```bash
python -m multicloud_mcp.server --config path/to/config.yaml
```

Alternatively, set:

```powershell
$env:MULTICLOUD_CONFIG_PATH="path\to\config.yaml"
```

## MCP tool model

The server exposes two categories of tools:

1. **Provider-native tools** — discovered from AWS/Azure adapters and routed through `ProviderRouter`.
2. **Multicloud-native tools** — implemented directly under `src/multicloud_mcp/tools/`.

This separation is intentional: cloud-specific integrations remain specialized, while cross-cloud behavior is implemented once in the multicloud layer.

## Testing

Run the complete test suite:

```bash
python -m pytest
```

The project's pytest configuration uses coverage options, so `pytest-cov` must be installed.

Run individual areas:

```bash
python -m pytest tests/test_providers.py
python -m pytest tests/test_multicloud_tools.py
python -m pytest tests/integration/test_end_to_end.py
```

Static analysis:

```bash
python -m mypy --strict src
python -m ruff check .
```

Auto-fix safe Ruff issues:

```bash
python -m ruff check . --fix
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Docker

A `Dockerfile` is included in the repository. Build the image from the repository root:

```bash
docker build -t multicloud-mcp-server .
```

Before deploying the image, provide the provider configuration and credentials through your normal secrets/configuration mechanism. Do not bake cloud credentials into the image.

## Observability

The server uses structured logging and provider health monitoring. Operationally relevant components include:

- `logging_config.py`
- `health.py`
- provider health checks
- circuit-breaker state
- HTTP health endpoints implemented by the server layer

See [docs/OPERATIONS.md](docs/OPERATIONS.md).

## Security principles

- Keep provider credentials outside source control.
- Prefer workload identity / managed identity / role-based authentication over static credentials where the provider integration supports it.
- Grant read-only permissions by default for discovery, posture, compliance, and FinOps use cases.
- Apply least privilege to every provider adapter.
- Never log secrets, access keys, tokens, or credential payloads.
- Protect the HTTP transport when exposed outside localhost/private networks.

## Extending the project

To add a new cloud provider:

1. implement the provider contract defined in `providers/base.py`;
2. implement tool discovery and invocation;
3. add provider health handling;
4. register the provider during server initialization;
5. add unit and integration tests;
6. update the resource mapper if new provider resource types require normalization.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Components, responsibilities, flows, and extension model. |
| [Features](docs/FEATURES.md) | Functional capabilities and current provider scope. |
| [Tools](docs/TOOLS.md) | Native MCP tools and routing behavior. |
| [Configuration](docs/CONFIGURATION.md) | Configuration loading and credential guidance. |
| [Operations](docs/OPERATIONS.md) | Health, logging, deployment, troubleshooting. |
| [Development](docs/DEVELOPMENT.md) | Development environment, testing, linting, type checking. |
| [Contributing](CONTRIBUTING.md) | Contribution workflow and coding expectations. |

## Roadmap

Potential evolution areas:

- GCP provider adapter;
- broader normalized FinOps datasets;
- consolidated amortized-cost reporting;
- forecasting and optimization recommendations;
- normalized tagging/label dimensions;
- richer security/compliance frameworks;
- provider capability discovery;
- persistent caching;
- metrics/tracing integration;
- production authentication/authorization for HTTP transport.

## License

See [LICENSE](LICENSE).
