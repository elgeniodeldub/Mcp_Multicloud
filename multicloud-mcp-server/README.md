# Multicloud MCP Server

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

The live FinOps architecture is documented in [docs/finops.md](docs/finops.md).
