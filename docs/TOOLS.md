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

## `finops__forecast`

```json
{"start_date": "2026-11-02", "end_date": "2026-12-01", "providers": ["aws", "azure"]}
```

Forecast spend from AWS Cost Explorer (`GetCostForecast`, 80% prediction interval) and Azure Cost Management (`forecast`). Without dates it covers tomorrow to the end of the current month. Dates cannot be in the past.

## `finops__anomalies`

```json
{"period": "last_30_days", "min_impact": 25}
```

AWS returns Cost Anomaly Detection findings with root causes (requires an anomaly monitor). Azure has no anomaly query API, so daily actual cost is scored against a 28-day median/MAD baseline and days with a robust z-score of 3 or more are reported (`source: "statistical"`). Results are sorted by absolute impact.

## `finops__budgets`

```json
{"alert_threshold_pct": 80}
```

AWS Budgets and Azure Consumption budgets with limit, actual, forecast, `utilization_pct`, `forecast_pct`, and `alert` (utilization at or above the threshold, or forecast over 100%).

## `finops__cost_by_tag`

```json
{"tag_key": "team", "period": "month_to_date"}
```

Actual spend grouped by the values of one tag key. On AWS the tag must be activated as a cost allocation tag. Untagged spend appears as `(untagged)`.

All four tools are read-only, run providers concurrently, and return `partial` / `providers_failed` when one provider fails.

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
