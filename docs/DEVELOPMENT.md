# Development

```bash
cd multicloud-mcp-server
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
```

Run tests:

```bash
python -m pytest
python -m pytest tests/test_security.py
python -m pytest tests/test_router.py
python -m pytest tests/test_providers.py
python -m pytest tests/test_multicloud_tools.py
python -m pytest tests/integration/test_end_to_end.py
```

Static analysis:

```bash
python -m ruff check .
python -m mypy --strict src
```

Principles: preserve stable tool names, keep provider-specific logic in adapters, keep cross-cloud logic in native tools, test security/FinOps deterministically, and never commit real credentials.
