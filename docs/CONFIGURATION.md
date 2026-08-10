# Configuration

## Overview

Configuration is implemented in `src/multicloud_mcp/config.py` using Pydantic models/settings.

Confirmed capabilities include:

- YAML configuration files;
- environment-variable interpolation/resolution;
- `Settings.from_yaml(path)`;
- `Settings.load()`;
- configuration selection through `MULTICLOUD_CONFIG_PATH`;
- CLI `--config` support.

## Selecting a configuration file

### Environment variable

PowerShell:

```powershell
$env:MULTICLOUD_CONFIG_PATH="C:\path\to\config.yaml"
python -m multicloud_mcp.server
```

Linux/WSL:

```bash
export MULTICLOUD_CONFIG_PATH=/path/to/config.yaml
python -m multicloud_mcp.server
```

### CLI

```bash
python -m multicloud_mcp.server --config /path/to/config.yaml
```

When `--config` is provided, the server loads the explicit YAML file. Otherwise it uses `Settings.load()`.

## Cloud credentials

Do not store AWS/Azure credentials in committed YAML files.

Use the normal credential chain supported by the underlying provider integration, for example:

- environment variables;
- local developer identity/CLI sessions;
- IAM roles/workload identity;
- Azure managed identity/service principals;
- external secret stores.

The exact credential mechanism is ultimately determined by the AWS/Azure provider integration used by the adapter.

## Least privilege

For discovery/FinOps/security posture use cases, start with read-only access and add permissions only when a specific tool requires them.

Recommended principles:

- separate credentials per environment;
- avoid personal long-lived keys in production;
- rotate static secrets when unavoidable;
- never commit `.env` files containing secrets;
- never print tokens/keys in structured logs.

## Configuration schema maintenance

`config.py` is the source of truth for the exact YAML schema.

Whenever a settings model changes:

1. update this document;
2. update any example config in the repository;
3. update tests for config loading;
4. verify environment-variable expansion;
5. run `mypy`, `ruff`, and `pytest`.
