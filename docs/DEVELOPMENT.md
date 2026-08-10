# Development Guide

## Environment

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Development tools:

```powershell
python -m pip install pytest pytest-cov mypy ruff
```

### Linux / WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-cov mypy ruff
```

## Test suite

All tests:

```bash
python -m pytest
```

Providers:

```bash
python -m pytest tests/test_providers.py
```

Native tools:

```bash
python -m pytest tests/test_multicloud_tools.py
```

Integration:

```bash
python -m pytest tests/integration/test_end_to_end.py
```

## Coverage

The repository's pytest configuration expects `pytest-cov`.

A missing plugin produces an error similar to:

```text
unrecognized arguments: --cov=multicloud_mcp --cov-report=term-missing --cov-report=xml
```

Install it with:

```bash
python -m pip install pytest-cov
```

## Type checking

```bash
python -m mypy --strict src
```

Do not suppress strict typing errors globally. Prefer typing provider boundaries and narrowing `Exception`/union results explicitly.

## Linting

```bash
python -m ruff check .
```

Safe auto-fixes:

```bash
python -m ruff check . --fix
```

Formatting/lint rules should be kept consistent with `pyproject.toml` and `.pre-commit-config.yaml`.

## Development workflow

Recommended flow:

1. create/update implementation;
2. add focused unit tests;
3. add/update integration mock if routing behavior changes;
4. run targeted pytest tests;
5. run the complete suite;
6. run `mypy --strict`;
7. run Ruff;
8. update README/docs when public behavior changes.

## Test strategy

### Provider tests

Validate:

- initialization;
- tool discovery;
- tool invocation;
- timeout behavior;
- health behavior;
- shutdown/cleanup.

### Native tool tests

Validate each native tool independent of real clouds using mocked providers/router data.

### End-to-end tests

Use provider mocks implementing the common provider contract. Validate the full chain:

```text
MCP server -> native/provider tool -> router -> mock provider -> response
```

## Definition of done

A change is complete when:

- behavior is implemented;
- there are no `NotImplementedError` placeholders in the changed path;
- tests cover success and relevant failure paths;
- `pytest` passes;
- `mypy --strict` passes;
- Ruff passes;
- docs reflect externally visible behavior.
