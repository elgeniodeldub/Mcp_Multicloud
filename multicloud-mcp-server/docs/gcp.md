# GCP support

The server supports a first read-only GCP FinOps integration for public list
prices only.

## Scope

`finops__gcp_list_prices` reads the Google Cloud Cloud Billing Catalog API and
returns public SKU pricing. It does not query actual usage or invoiced spend,
and it does not use BigQuery, Cloud Billing exports, discounts, commitments,
credits, taxes, or amortization.

Configure an API key in the process environment:

```powershell
$env:GCP_BILLING_API_KEY="your-catalog-api-key"
```

The key is never stored in YAML or returned by the tool. The Cloud Billing API
must be enabled in the Google Cloud project associated with the key.

Example MCP arguments:

```json
{
  "service_id": "services/6F81-5844-456A",
  "region": "us-central1",
  "currency": "USD",
  "page_size": 100
}
```

The service ID must come from the Cloud Billing Catalog. GCP actual-cost
queries are intentionally out of scope until a separate billing-data design is
approved.
