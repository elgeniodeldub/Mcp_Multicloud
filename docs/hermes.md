# Hermes Agent integration

Hermes Agent can connect to this repository as an external MCP server. The
recommended profile uses stdio and exposes only semantic, read-only tools.

Install the package first:

```bash
cd multicloud-mcp-server
python -m pip install -e .
```

Then copy the appropriate example from `multicloud-mcp-server/examples/hermes/`
to the Hermes `mcp_servers` configuration. The semantic profile includes:

- `multicloud__*` discovery, security, compliance, and provider health tools;
- `finops__get_cost`, `finops__breakdown`, `finops__compare`;
- `finops__get_actual_costs` for AWS/Azure actual non-amortized spend;
- `finops__compare_list_prices` for AWS/Azure public-price estimates;
- `finops__gcp_list_prices` for GCP public catalog prices only.

Raw `aws__*` and `azure__*` tools are disabled in the semantic profile and
available only in the advanced profile.

GCP is not a full connected provider. `GCP_BILLING_API_KEY` enables only public
Cloud Billing Catalog lookup. GCP resource discovery and actual GCP billing are
unsupported; the agent must report actual GCP spend as unsupported.

The repository HTTP endpoint currently exposes stateless JSON-RPC at
`POST /mcp`, but it is not advertised as Hermes Streamable HTTP compatible yet.
Use stdio with Hermes. The optional local smoke test is:

```bash
python scripts/hermes_smoke_test.py
```

It exits with status 2 when Hermes is not installed and never installs Hermes or
prints credentials.
