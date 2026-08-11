# Hermes Agent integration

Hermes Agent's current MCP client supports local stdio servers and remote
HTTP/StreamableHTTP servers, discovers tools at startup, and supports per-server
`tools.include` and `tools.exclude` filters.

The examples in `examples/hermes/` use the actual package entrypoint. Install
the package first with `python -m pip install -e .`:

```bash
python -m multicloud_mcp.server --config examples/hermes/multicloud.semantic.yaml
```

Hermes exposes discovered tools with its own prefix, such as
`mcp_multicloud_semantic_finops_get_cost`.

## Profiles

`config.semantic.yaml` is the recommended profile. It includes native read-only
tools for discovery, security, compliance, normalized FinOps, actual AWS/Azure
spend, AWS/Azure list-price estimates, and GCP public catalog prices. Raw
`aws__*` and `azure__*` passthrough tools are disabled.

`config.advanced.yaml` enables raw AWS/Azure passthrough. Use it only when
low-level provider tools are explicitly needed and keep the server read-only
policy enabled for agent use.

## Credentials and GCP boundary

AWS and Azure credentials are consumed by provider adapters. Do not put them in
this repository or in tool arguments. Hermes filters the environment passed to
stdio subprocesses, so explicitly configure only variables required by the
provider.

`GCP_BILLING_API_KEY` enables only `finops__gcp_list_prices`: public Cloud
Billing Catalog SKU/list-price lookup. It does not enable a GCP provider,
resource discovery, actual GCP billing, BigQuery exports, or GCP MCP passthrough.

## HTTP status

The repository's HTTP endpoint currently provides a stateless JSON-RPC endpoint
at `POST /mcp`, with Bearer authentication when enabled. It is not advertised
as Hermes-compatible Streamable HTTP because the current server does not
implement the MCP Streamable HTTP session/transport contract required by
Hermes' HTTP client. Use stdio with Hermes today.

## Agent scenarios

| Intent | Preferred tool | Limitation |
|---|---|---|
| List compute resources across AWS/Azure | `multicloud__discover_resources` | GCP resources are not included |
| Show actual AWS/Azure spend | `finops__get_actual_costs` or `finops__get_cost` | GCP actual spend unsupported |
| Compare public AWS/Azure prices | `finops__compare_list_prices` | Estimator, not invoice data |
| Show public GCP SKU prices | `finops__gcp_list_prices` | Catalog list prices only |
| Ask for actual GCP spend | No supported tool | Must report unsupported |
| Request low-level AWS operation | `aws__*` | Advanced passthrough only |

Independent read-only AWS/Azure cost queries are orchestrated concurrently;
provider concurrency controls remain active. GCP catalog responses include
`returned_count`, `truncated`, and `next_cursor` metadata.

Hermes is optional and is not a runtime dependency. Run `hermes mcp test <name>`
when Hermes is installed. HTTP validation remains unsupported until Streamable
HTTP is implemented.
