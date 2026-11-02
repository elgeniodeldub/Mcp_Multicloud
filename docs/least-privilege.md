# Least-privilege cloud identities

Give the server identities that can **read** cost and inventory data and nothing
else. The `read_only` tool policy is a second line of defence; IAM and RBAC are
the first. Prefer workload identities over long-lived keys:

| Where it runs | AWS | Azure |
|---|---|---|
| AWS (ECS/EKS/EC2) | Task role / IRSA / instance profile | Workload identity federation |
| Azure (AKS/Container Apps/VM) | IAM Roles Anywhere or OIDC federation | Managed identity |
| Developer laptop | `aws sso login` (short-lived) | `az login` (short-lived) |

Never put access keys, client secrets, or API keys in `config.yaml`; use the
environment or your platform's secret store.

## AWS IAM policy (native FinOps tools)

Covers `finops__get_actual_costs`, `finops__get_cost`, `finops__breakdown`,
`finops__compare`, `finops__forecast`, `finops__anomalies`, `finops__budgets`,
and `finops__cost_by_tag`.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CostExplorerRead",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ce:GetAnomalies",
        "ce:GetDimensionValues",
        "ce:GetTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BudgetsRead",
      "Effect": "Allow",
      "Action": ["budgets:ViewBudget"],
      "Resource": "arn:aws:budgets::*:budget/*"
    }
  ]
}
```

`sts:GetCallerIdentity` (used to find the account ID for Budgets) needs no
permission. In AWS Organizations, attach the policy in the management (payer)
account to see linked-account costs. For provider passthrough tools add the
AWS managed `ReadOnlyAccess` or `ViewOnlyAccess` policy, never `PowerUserAccess`.

## Azure RBAC

Assign at the narrowest scope that covers what you need to report on
(subscription, or management group for several subscriptions):

| Need | Built-in role |
|---|---|
| Costs, forecasts, anomalies (`finops__*`) | **Cost Management Reader** |
| Budgets (`finops__budgets`) | **Cost Management Reader** (budgets read) |
| Resource discovery, security posture via Azure MCP | **Reader** |
| Security posture details (Defender) | **Security Reader** |

```bash
az role assignment create \
  --assignee "<managed-identity-principal-id>" \
  --role "Cost Management Reader" \
  --scope "/subscriptions/<subscription-id>"
```

Avoid **Contributor** and **Owner**. If you need write operations through Azure
MCP, run a separate server instance with its own identity and keep this one
read-only.

## GCP

`finops__gcp_list_prices` uses an API key restricted to the **Cloud Billing API**
(set an API restriction on the key). It needs no IAM role and cannot read
project data.

## Checklist

- [ ] One identity per environment; no shared keys between dev and prod.
- [ ] Only the roles above; review with IAM Access Analyzer / Azure access reviews.
- [ ] `security.tool_policy.mode: read_only` for any agent-facing deployment.
- [ ] HTTP behind TLS with `authentication.type: oidc` and per-tool scopes.
- [ ] CloudTrail and Azure Activity Log enabled to audit what the identity did.
