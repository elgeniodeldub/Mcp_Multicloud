# Configuration

Configuration uses Pydantic plus YAML/environment variables.

## Loading

```text
MULTICLOUD_CONFIG_PATH
```

Supported interpolation:

```text
${VAR}
${VAR:-default}
```

## Security example

```yaml
server:
  transport: http
  http:
    host: 127.0.0.1
    port: 8080

security:
  authentication:
    enabled: true
    type: bearer
    api_key_env: MULTICLOUD_API_KEY
    protect_metrics: true

  cors:
    enabled: false
    allowed_origins: []

  max_request_size_bytes: 1048576

  rate_limit:
    enabled: true
    requests_per_minute: 60

  tool_policy:
    mode: read_only
```

Provider configuration includes `enabled`, `command`, `args`, `env`, `namespace`, `health_check_interval`, `timeout`, and `description`.

Namespaces cannot contain `__`.
