# Operations

## Runtime modes

The server supports both `stdio` and HTTP transport.

Use:

```bash
python -m multicloud_mcp.server --help
```

for the exact options supported by the current checkout.

## Health monitoring

`health.py` monitors providers and maintains circuit-breaker state.

Operationally, monitor for:

- provider health failures;
- transitions to OPEN circuit state;
- repeated timeouts;
- initialization errors;
- partial results when only one provider is healthy.

## Structured logs

The project uses `structlog`.

Useful event fields should include, where applicable:

- provider;
- MCP tool;
- operation;
- duration;
- result status;
- exception type;
- correlation/request identifier;
- circuit-breaker state.

Never include credentials or raw authorization headers.

## HTTP deployment

The HTTP transport uses Starlette/Uvicorn.

For production exposure:

- bind to a private interface/network unless public access is explicitly required;
- place authentication/authorization in front of the service;
- enforce TLS;
- restrict CORS to intended clients;
- configure request limits/timeouts;
- run behind a production ingress/reverse proxy where appropriate;
- export logs to centralized observability.

## Docker

Build:

```bash
docker build -t multicloud-mcp-server .
```

Do not copy cloud secrets into the image. Inject credentials at runtime.

## Troubleshooting

### `python` is not found

On Windows:

```powershell
py --version
python --version
where.exe python
```

If Python is installed but not on PATH, restart the terminal/VS Code after updating PATH.

### Pytest rejects `--cov`

Symptom:

```text
unrecognized arguments: --cov=... --cov-report=...
```

Install the coverage plugin:

```bash
python -m pip install pytest-cov
```

Then retry:

```bash
python -m pytest
```

### Provider tools are missing

Check:

1. provider configuration;
2. provider initialization logs;
3. provider health status;
4. underlying MCP/API connectivity;
5. provider tool discovery;
6. router tool indexing.

### Provider call times out

Check:

- configured provider timeout;
- underlying provider process/service;
- cloud authentication;
- network access;
- circuit-breaker status.

## Release checklist

Before releasing:

```bash
python -m pytest
python -m mypy --strict src
python -m ruff check .
```

Also verify:

- Docker image builds;
- stdio startup;
- HTTP startup;
- AWS mocked/provider integration flow;
- Azure mocked/provider integration flow;
- native multicloud tool discovery;
- graceful shutdown.
