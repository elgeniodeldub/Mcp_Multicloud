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

## `finops__playbooks`

```json
{"action": "search", "query": "savings plans reservations", "limit": 3}
```

```json
{"action": "get", "id": "commitment-based-discounts"}
```

Serves FinOps Framework playbooks packaged with the server. `action` is `list`
(default), `search`, or `get`. `list` and `search` accept the filters `domain`,
`capability`, `phase` (`inform`, `optimize`, `operate`), and `provider`
(`aws`, `azure`, `gcp`). `search` ranks by keyword overlap with title, tags,
capabilities, summary, and body; `limit` is 1-10 (default 5). `get` returns the
full Markdown runbook.

Playbooks shipped: `cost-allocation-tagging`, `anomaly-management`,
`budgeting-and-forecasting`, `rightsizing-compute`,
`idle-and-orphaned-resources`, `commitment-based-discounts`,
`storage-optimization`, `unit-economics`, `showback-and-chargeback`,
`policy-and-governance`. Each one covers when to use it, signals, steps, KPIs,
and pitfalls, and lists the `finops__*` / `multicloud__*` tools that fetch the
data it needs (`related_tools`).

The result is labeled `content_type: "guidance"`. It reads no cloud account,
makes no network call, and contains no prices or discount rates. Invalid
arguments or an unknown `id` return `invalid_request`. Playbooks are aligned
with the FinOps Foundation framework; they are not endorsed by it.

Example questions and tool calls for each playbook: [PLAYBOOKS.md](PLAYBOOKS.md).

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
