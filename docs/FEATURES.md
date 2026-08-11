# Features

## Unified gateway
Single MCP-facing service for AWS and Azure with dynamic provider routing.

## FinOps
- `finops__get_actual_costs`: AWS Cost Explorer `UnblendedCost` + Azure Cost Management `PreTaxCost`.
- `finops__compare_list_prices`: illustrative public list-price comparison for compute/storage/database.
- `finops__gcp_list_prices`: public GCP SKU/list-price lookup through the Cloud Billing Catalog API.

GCP support is limited to public list prices. Actual GCP usage cost, BigQuery,
and Cloud Billing exports are intentionally out of scope.

## Discovery
`multicloud__discover_resources` supports compute, storage, database, and Kubernetes discovery using compatible provider-native listing tools.

## Resource mapping
`multicloud__map_resource` maps common AWS/Azure service equivalents.

## Security posture
`multicloud__security_posture` aggregates available IAM, role-assignment, exposure, security-group, findings, recommendations, and score capabilities.

## Compliance readiness
`multicloud__compliance_check` supports CIS/NIST-oriented assessment. It is not certification or attestation.

## HTTP security
Bearer auth, restrictive CORS, request size limit, per-IP rate limiting, request IDs, safe errors, security headers, audit logging, and redaction.

## Tool policy
Modes: `allow_all`, `read_only`.

## Observability
`/health`, `/metrics`, structured logging.
