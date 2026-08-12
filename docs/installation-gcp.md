# GCP installation manual

Maintained by **Carlos Razuri**.

## Scope and limitation

This repository does **not** implement a full GCP provider. GCP support is
limited to the native read-only tool `finops__gcp_list_prices`, which reads
public Cloud Billing Catalog list prices.

It does not provide GCP actual spend, resource discovery, raw GCP MCP
passthrough, BigQuery billing exports, discounts, credits, commitments, or
amortization.

## Prerequisites

- A Google Cloud project used to enable the Cloud Billing API.
- Google Cloud CLI or access to the Google Cloud Console.
- An API key restricted to the Cloud Billing API.

Enable the API with the Google Cloud CLI:

```powershell
gcloud services enable cloudbilling.googleapis.com --project "<project-id>"
```

Create an API key in the Google Cloud Console, restrict it to the Cloud Billing
API, and restrict its application usage according to your deployment. Do not
commit the key or place it in YAML.

## Configure the server

```powershell
$env:GCP_BILLING_API_KEY = "<catalog-api-key>"
multicloud-mcp-server --transport stdio
```

The key is read only from `GCP_BILLING_API_KEY`. It is never a tool argument,
logged value, or repository configuration value.

## Use the tool

```json
{
  "service_id": "services/6F81-5844-456A",
  "region": "us-central1",
  "currency": "USD",
  "page_size": 50
}
```

Use a conservative `page_size` to avoid flooding an agent context. Results are
public list prices and must not be interpreted as actual customer spend.

## Troubleshooting

- `GCP_BILLING_API_KEY is required`: set the variable in the same process that
  starts the MCP server.
- `403`: enable Cloud Billing API and check API-key restrictions.
- No actual GCP costs: this is expected; actual GCP billing is out of scope for
  the current integration.

## Official references

- [Public Cloud Billing Catalog API](https://docs.cloud.google.com/billing/v1/how-tos/catalog-api)
- [Google Cloud authentication](https://docs.cloud.google.com/docs/authentication)
