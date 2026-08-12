# Configuration

Maintained by **Carlos Razuri**. See the [cloud installation manuals](installation.md)
for AWS, Azure, and GCP setup without committing credentials.

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

## GCP list prices

GCP list-price lookup is enabled as a native FinOps tool and does not require a
GCP MCP provider process. Set the Cloud Billing Catalog API key outside the
configuration file:

```powershell
$env:GCP_BILLING_API_KEY="your-catalog-api-key"
```

The key is used only by `finops__gcp_list_prices`. This integration is limited
to public SKU/list prices; it does not provide actual usage cost and does not
use BigQuery or Cloud Billing exports.
