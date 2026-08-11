# MCP Tools

## `finops__get_actual_costs`

```json
{
  "start_date": "2026-08-01",
  "end_date": "2026-08-10",
  "granularity": "DAILY",
  "group_by": "SERVICE",
  "providers": ["aws", "azure"]
}
```

`end_date` is exclusive. Supported granularity: `DAILY`, `MONTHLY`. Supported grouping: `SERVICE`, `REGION`, `LINKED_ACCOUNT`. AWS uses `UnblendedCost`; Azure uses `ActualCost`/`PreTaxCost`.

## `finops__compare_list_prices`

```json
{
  "service_type": "compute",
  "region_aws": "us-east-1",
  "region_azure": "eastus",
  "specs": {"vcpu": 4, "memory_gb": 16}
}
```

Illustrative estimator only; not actual billing.

## `finops__gcp_list_prices`

```json
{
  "service_id": "services/6F81-5844-456A",
  "region": "us-central1",
  "currency": "USD",
  "page_size": 100
}
```

Queries public GCP SKU prices from the Cloud Billing Catalog API. The API key
must be provided through `GCP_BILLING_API_KEY`; it is never stored in YAML or
returned in the response. This tool does not query actual spend or use
BigQuery/billing exports.

## `multicloud__map_resource`
Maps a resource/service concept between AWS and Azure.

## `multicloud__list_providers`
Lists connected providers and health context.

## `multicloud__discover_resources`
Optional provider/resource-type filters; supports compute, storage, database, Kubernetes.

## `multicloud__security_posture`
Aggregates available provider security checks.

## `multicloud__compliance_check`
Framework: `CIS` or `NIST`. Current scope is readiness/assessment support.

## Provider-native tools
Discovered dynamically under `aws__*` and `azure__*`.
