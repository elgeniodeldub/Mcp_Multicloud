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
| `finops__get_cost` | Normalized AWS/Azure cost totals (FOCUS-aligned, effective or billed cost) |
| `finops__breakdown` | AWS/Azure cost by provider, account, service, category, or region |
| `finops__compare` | AWS/Azure cost differences between providers or periods |
| `finops__compare_list_prices` | Illustrative public list-price comparison |
| `finops__gcp_list_prices` | Native GCP public SKU/list-price lookup |
| `finops__playbooks` | FinOps Framework playbooks: list, search, and read step-by-step guidance |
| `finops__forecast` | AWS/Azure spend forecast to a future date |
| `finops__anomalies` | Cost anomalies (AWS Anomaly Detection, Azure statistical baseline) |
| `finops__budgets` | Budget limit, actual, forecast, and alerts |
| `finops__cost_by_tag` | Spend allocation by tag value |
| `multicloud__map_resource` | AWS/Azure service mapping |
| `multicloud__list_providers` | Provider status and health |
| `multicloud__discover_resources` | Cross-cloud resource discovery |
| `multicloud__security_posture` | Aggregated security posture |
| `multicloud__compliance_check` | CIS/NIST-oriented compliance readiness |

## Security

HTTP mode includes localhost binding by default (and refuses remote binding without authentication), static Bearer or OAuth 2.1 / OIDC JWT authentication with per-tool scopes, trusted-proxy handling, restrictive CORS, request-size limits, per-identity rate limiting (in-memory or Redis), request IDs, audit logging, redaction, security headers, safe error responses, and `allow_all` / default-deny `read_only` tool policies. See [least-privilege identities](docs/least-privilege.md).

The policy layer complements rather than replaces AWS IAM and Azure RBAC.

## FinOps

`finops__get_actual_costs` queries AWS Cost Explorer using `UnblendedCost` and Azure Cost Management using `PreTaxCost` / `ActualCost`. The result is labeled `actual_non_amortized`.

`finops__compare_list_prices` remains an illustrative estimator and does not represent invoiced, discounted, reserved, committed, credited, amortized, tax-adjusted, or privately negotiated spend.

`finops__gcp_list_prices` queries the Google Cloud Billing Catalog API for
public SKU pricing only. It does not query actual GCP spend, BigQuery, billing
exports, discounts, commitments, credits, taxes, or amortization. Configure
`GCP_BILLING_API_KEY` in the process environment; never store it in YAML.

`finops__playbooks` serves ten FinOps Framework playbooks packaged with the
server (allocation and tagging, anomalies, budgets and forecasts, rightsizing,
idle resources, commitments, storage, unit economics, showback/chargeback,
governance). Each playbook names the tools that fetch the data it needs, so an
agent can move from "what should we do" to "what do our numbers say". It reads
no cloud account and contains no prices. See [how to ask and use each playbook](docs/PLAYBOOKS.md).

## What it does not do

- **No changes to your cloud.** Native `finops__*` and `multicloud__*` tools are
  read-only. Provider passthrough tools can be limited with the `read_only`
  policy, which complements IAM and RBAC and does not replace them.
- **No invoiced or negotiated prices.** List-price tools are illustrative. Actual
  cost tools return what the provider APIs report, not your contract terms.
- **No actual GCP spend.** GCP is limited to the public price catalog.
- **No certification.** `multicloud__compliance_check` reports readiness gaps;
  it is not an audit, attestation, or certification.
- **No legal, tax, or accounting advice.** Playbooks describe mechanics; your
  finance, legal, and tax advisers decide.
- **No natural-language reasoning.** The connected LLM or agent interprets
  results; the server fetches data and returns structured results.

See [PRIVACY.md](PRIVACY.md) for what the server sends, logs, and stores.

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
- [FinOps playbooks: how to ask and use them](docs/PLAYBOOKS.md)
- [Configuration](docs/CONFIGURATION.md)
- [Security](docs/SECURITY.md)
- [Operations](docs/OPERATIONS.md)
- [Development](docs/DEVELOPMENT.md)
- [GCP list-price support](docs/gcp.md)
- [Cloud installation manuals](docs/installation.md)

## License

Apache 2.0. See `multicloud-mcp-server/LICENSE`.
