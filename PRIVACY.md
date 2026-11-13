# Privacy and data handling

What Multicloud MCP Server reads, sends, logs, and stores, so you can decide
where to run it. This describes the code in this repository. You run the
server yourself; the maintainer operates no hosted instance and receives no
data from your deployment.

## Summary

- The server runs in your environment, with the cloud identities you give it.
- It calls only the cloud and identity endpoints needed for the tools you enable.
- Audit logs record which tool ran and its outcome, not the tool arguments or
  results.
- FinOps cost results are cached for a short time (5 minutes by default), in
  memory or in a Redis instance you configure.
- There is no telemetry, analytics, or update check. OpenTelemetry tracing is
  off unless you enable it and point it at your own collector.

## Data the server reads

| Source | When | What |
|---|---|---|
| AWS APIs (for example Cost Explorer, Budgets, and those called by the AWS MCP server) | AWS tools enabled | Cost, forecast, anomaly, budget, and resource data allowed by the IAM identity |
| Azure Resource Manager (`management.azure.com`) and the Azure MCP server | Azure tools enabled | Cost, forecast, budget, and resource data allowed by the RBAC identity |
| Google Cloud Billing Catalog API (`cloudbilling.googleapis.com`) | `finops__gcp_list_prices` called | Public SKU prices only; no project or billing data |
| Packaged playbook files | `finops__playbooks` called | Static Markdown shipped in the package; no network call |

Credentials come from the standard provider chains (AWS SDK credential chain,
`DefaultAzureCredential`) and from environment variables such as
`GCP_BILLING_API_KEY` and the HTTP API key variable. They are never read from
YAML, returned in results, or written to logs. Use
[least-privilege identities](docs/least-privilege.md).

## Data the server sends

- **To cloud providers:** the query parameters of each tool call (dates,
  grouping, filters, tag keys) over HTTPS to the provider APIs above.
- **To upstream MCP servers:** provider passthrough tool calls and their
  arguments go to the AWS and Azure MCP server processes the server starts
  locally; those processes then call their provider APIs.
- **To your identity provider:** in OIDC mode, the server fetches the issuer's
  discovery document and JWKS over HTTPS to validate tokens.
- **To optional services you configure:** Redis (cache and rate-limit
  counters) and an OpenTelemetry collector (traces).

Nothing is sent to the maintainer or to any other third party.

## What is logged

Each tool execution writes one structured audit event with: request ID, tool
name, provider, transport, caller (the token subject in OIDC mode), success,
partial-result flag, duration, and error code. Tool arguments and results are
not logged. Tokens are never logged. Log storage and retention follow your
logging platform.

## What is stored

- **FinOps result cache:** cost query results, keyed by the query, kept for
  `cache.ttl_seconds` (default 300). Backend: process memory, or Redis when
  `cache.backend: redis`. Partial results stay in local memory only.
- **Rate-limit counters:** per token subject, or per client IP when
  unauthenticated, in memory or Redis, for the rate-limit window.
- **Tool catalog cache:** upstream tool metadata, in memory.

The server has no database and keeps no conversation history.

## The LLM client

Results returned to the MCP client (for example an AI assistant) are handled by
that client and its model provider under their own terms. Cost data you query
reaches the model you connected; choose the client accordingly.

## Reporting a concern

Report privacy or security issues as described in [SECURITY.md](SECURITY.md).
