# Multicloud MCP Server

Maintained by **Carlos Razuri**.

Unified Model Context Protocol (MCP) gateway for AWS and Azure with native FinOps, resource discovery, security posture, compliance readiness, resource mapping, health monitoring, and secure HTTP transport.

## Providers

| Provider | Status |
|---|---|
| AWS | Supported |
| Azure | Supported |
| GCP | List-price catalog supported |

## Native MCP tools

| Tool | Purpose |
|---|---|
| `finops__get_actual_costs` | Actual non-amortized AWS/Azure billing data |
| `finops__compare_list_prices` | Illustrative public list-price comparison |
| `finops__gcp_list_prices` | Native GCP public SKU/list-price lookup |
| `multicloud__map_resource` | AWS/Azure service mapping |
| `multicloud__list_providers` | Provider status and health |
| `multicloud__discover_resources` | Cross-cloud resource discovery |
| `multicloud__security_posture` | Aggregated security posture |
| `multicloud__compliance_check` | CIS/NIST-oriented compliance readiness |

## Security

HTTP mode includes localhost binding by default, optional Bearer authentication, restrictive CORS, request-size limits, rate limiting, request IDs, audit logging, redaction, security headers, safe error responses, and `allow_all` / `read_only` tool policies.

The policy layer complements rather than replaces AWS IAM and Azure RBAC.

## FinOps

`finops__get_actual_costs` queries AWS Cost Explorer using `UnblendedCost` and Azure Cost Management using `PreTaxCost` / `ActualCost`. The result is labeled `actual_non_amortized`.

`finops__compare_list_prices` remains an illustrative estimator and does not represent invoiced, discounted, reserved, committed, credited, amortized, tax-adjusted, or privately negotiated spend.

`finops__gcp_list_prices` queries the Google Cloud Billing Catalog API for
public SKU pricing only. It does not query actual GCP spend, BigQuery, billing
exports, discounts, commitments, credits, taxes, or amortization. Configure
`GCP_BILLING_API_KEY` in the process environment; never store it in YAML.

## Architecture

```text
MCP Client / AI Agent
        |
   stdio / HTTP
        |
MulticloudMCPServer
        |
  +-----+---------------------+
  |                           |
Native tools              ProviderRouter
multicloud__/finops__          |
                          +----+----+
                          |         |
                         AWS       Azure
```

The upstream LLM/client performs natural-language reasoning. The MCP server is the execution and cloud-data access layer.

## HTTP endpoints

```text
POST /mcp
GET  /health
GET  /metrics
```

Do not expose the built-in HTTP server directly to the public Internet without authentication, TLS termination, network controls, and least-privilege provider identities.

## Development

```bash
cd multicloud-mcp-server
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest
python -m ruff check .
python -m mypy --strict src
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Features](docs/FEATURES.md)
- [Tools](docs/TOOLS.md)
- [Configuration](docs/CONFIGURATION.md)
- [Security](docs/SECURITY.md)
- [Operations](docs/OPERATIONS.md)
- [Development](docs/DEVELOPMENT.md)
- [GCP list-price support](docs/gcp.md)
- [Cloud installation manuals](docs/installation.md)

## License

Apache 2.0. See `multicloud-mcp-server/LICENSE`.
