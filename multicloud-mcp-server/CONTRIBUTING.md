# Contributing to Multicloud MCP Server

Please read our detailed [Contributing Guide](docs/contributing.md).

## Quick Start

```bash
uv pip install -e ".[dev]"
pre-commit install
pytest
```

Antes de abrir un PR ejecuta también `python -m ruff check .`, `python -m ruff format --check .`, `python -m mypy --strict src` y `python -m build`. No incluyas secretos, archivos `.env`, credenciales cloud ni certificados. Los cambios de dependencias deben estar justificados.
