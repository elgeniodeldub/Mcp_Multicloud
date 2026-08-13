# Multicloud MCP Server

Maintained by **Carlos Razuri**.

This directory contains the Python implementation. The canonical project documentation lives at the repository root:

- `../README.md`
- `../docs/ARCHITECTURE.md`
- `../docs/FEATURES.md`
- `../docs/TOOLS.md`
- `../docs/CONFIGURATION.md`
- `../docs/SECURITY.md`
- `../docs/OPERATIONS.md`
- `../docs/DEVELOPMENT.md`

## Quick start

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
multicloud-mcp-server --transport stdio
```

## Quality

```bash
python -m pytest
python -m ruff check .
python -m mypy --strict src
```

HTTP defaults to `127.0.0.1`. Use `examples/config.secure.yaml` for hardened HTTP configuration.

The default AWS raw MCP passthrough is disabled because the configured external
`awslabs.core-mcp-server` package is not currently compatible with the MCP
dependency set. Native AWS FinOps tools remain available through Cost Explorer.

The live FinOps architecture is documented in [docs/finops.md](docs/finops.md).
Hermes Agent integration is documented in [docs/hermes.md](docs/hermes.md).
GCP list-price support is available through `finops__gcp_list_prices`. It uses
the Google Cloud Billing Catalog API only; it does not use BigQuery, billing
exports, or actual-cost data. See [GCP support](docs/gcp.md).

## Cloud installation manuals

- [AWS](docs/installation-aws.md)
- [Azure](docs/installation-azure.md)
- [GCP](docs/installation-gcp.md)
- [All cloud manuals](docs/installation.md)
