# Cloud installation manuals

These manuals are maintained by **Carlos Razuri** and describe the minimum
configuration required to connect the Multicloud MCP Server to each cloud.

- [AWS](installation-aws.md): Cost Explorer and optional AWS MCP passthrough.
- [Azure](installation-azure.md): Cost Management and optional Azure MCP passthrough.
- [GCP](installation-gcp.md): public Cloud Billing Catalog list prices only.

All credentials must be provided through the environment, local cloud login,
or a managed identity. Never commit `.env` files, access keys, service-principal
secrets, API keys, or credential JSON files.

## Common server setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run native tools over stdio:

```powershell
multicloud-mcp-server --transport stdio
```

For HTTP, use the secure example and configure Bearer authentication before
exposing the endpoint:

```powershell
$env:MULTICLOUD_API_KEY = "replace-me"
multicloud-mcp-server --config examples/config.secure.yaml
```

## Maintainer

Carlos Razuri — personal multicloud FinOps and MCP project documentation.
