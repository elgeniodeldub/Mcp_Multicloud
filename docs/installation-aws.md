# AWS installation manual

Maintained by **Carlos Razuri**.

## Scope

AWS support has two separate paths:

1. Native FinOps tools use the AWS Cost Explorer API through `boto3`.
2. Optional `aws__*` passthrough tools use an external AWS MCP server.

The default configuration keeps the external AWS passthrough disabled because
the previously configured package is not reliably compatible with the current
MCP dependency set. Native AWS FinOps remains available.

## Prerequisites

- Python 3.11 or newer supported by the project.
- An AWS account with Cost Explorer enabled.
- Credentials configured through the AWS standard credential chain.

For local Windows testing, the AWS shared files normally live under
`%USERPROFILE%\.aws`. Do not copy them into the repository.

## Minimum IAM policy for native FinOps

Attach a read-only policy to the test identity. The essential permission is:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadCostExplorer",
      "Effect": "Allow",
      "Action": ["ce:GetCostAndUsage"],
      "Resource": "*"
    }
  ]
}
```

For an AWS Organization, run the query from the management/payer account or
grant the identity access to the account whose Cost Explorer data it must read.
Linked-account visibility is governed by AWS billing access and IAM policy.

## Configure credentials

Preferred local options are AWS CLI login, a shared profile, or an approved
workload identity. Example with a named profile:

```powershell
$env:AWS_PROFILE = "finops-readonly"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

Validate without printing secrets:

```powershell
aws sts get-caller-identity
```

The server does not accept AWS access keys as MCP tool arguments.

## Enable native AWS FinOps

Native tools use Cost Explorer automatically when AWS credentials are present:

```text
finops__get_actual_costs
finops__get_cost
finops__breakdown
finops__compare
```

These are read-only live queries. They are not CUR, exports, BigQuery, or
amortized-cost ingestion.

## Optional AWS passthrough

Keep this disabled unless an external AWS MCP package has been independently
validated with the current MCP SDK. If enabled, configure its command and
arguments explicitly in a local, ignored override such as `config.local.yaml`.

## Troubleshooting

- `AccessDenied`: verify `ce:GetCostAndUsage`, billing access, and the active
  AWS profile.
- Empty or delayed data: Cost Explorer can have provider-side reporting delay;
  verify the requested date range.
- Wrong account: run `aws sts get-caller-identity` with the same environment
  used to start the MCP server.

## Official references

- [AWS Cost Explorer access control](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-access.html)
- [AWS Cost Explorer service authorization](https://docs.aws.amazon.com/service-authorization/latest/reference/list_awscostexplorerservice.html)
