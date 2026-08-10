# Contributing

Thank you for contributing to Multicloud MCP Server.

## Principles

- Keep provider-specific behavior inside provider adapters.
- Implement cross-cloud orchestration in native multicloud tools.
- Depend on provider abstractions rather than provider internals.
- Preserve tool namespaces and avoid collisions.
- Prefer least-privilege cloud access.
- Do not add secrets, tokens, cloud keys, or customer data to tests/examples.

## Setup

```bash
python -m venv .venv
python -m pip install -e .
python -m pip install pytest pytest-cov mypy ruff
```

Activate the virtual environment using the command appropriate for your OS.

## Before submitting a change

Run:

```bash
python -m pytest
python -m mypy --strict src
python -m ruff check .
```

## Adding a provider

A provider contribution should include:

- implementation of the provider base contract;
- tool discovery;
- tool invocation;
- health checking;
- timeout handling;
- unit tests;
- integration mock coverage;
- documentation update.

## Adding a multicloud tool

A native tool contribution should include:

- implementation under `src/multicloud_mcp/tools/`;
- MCP definition/input schema;
- server registration;
- dispatch implementation;
- unit tests;
- documentation in `docs/TOOLS.md`.

## Coding style

- type public/internal boundaries explicitly;
- keep async provider operations non-blocking;
- use structured logs rather than ad-hoc `print()` calls;
- return actionable errors;
- avoid catching broad exceptions unless the boundary intentionally normalizes provider failures;
- keep secrets out of logs.

## Documentation

Update documentation whenever a change modifies:

- CLI behavior;
- config schema;
- tool names/schemas;
- provider support;
- transport behavior;
- health behavior;
- deployment requirements.
