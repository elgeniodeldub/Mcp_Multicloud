# Azure installation manual

Maintained by **Carlos Razuri**.

## Scope

Azure support has two separate paths:

1. Native FinOps tools use the Azure Cost Management Query API.
2. Optional `azure__*` passthrough tools use the official Azure MCP server.

The tested passthrough configuration uses `@azure/mcp@2.0.4` with the
required `server start` arguments. Version `2.0.5` is currently avoided in the
Windows configuration because it was observed to terminate with `0xC00000FD`.

## Prerequisites

- An Azure subscription.
- Azure CLI installed for local authentication, or an approved service
  principal/workload identity for automation.
- The subscription ID and tenant ID available as environment variables when
  required.

## Local authentication

Interactive developer login:

```powershell
az login
az account set --subscription "<subscription-id>"
az account show --query "{subscription:id,tenant:tenantId,state:state}"
```

For a non-interactive environment, use a service principal or workload
identity according to your organization policy. Never put the client secret in
YAML or an MCP tool argument.

```powershell
$env:AZURE_SUBSCRIPTION_ID = "<subscription-id>"
$env:AZURE_TENANT_ID = "<tenant-id>"
```

The native adapter uses `DefaultAzureCredential`, which can use Azure CLI
authentication locally and managed identity/workload identity in deployment.

## Minimum permissions for native FinOps

Grant the identity read access to cost data at the required scope. In Azure,
the exact role and scope depend on whether the query is made at subscription,
resource-group, management-group, or billing-account scope. Start with the
least-privileged built-in billing reader role approved by your tenant and
verify that it can read Cost Management query data for the target subscription.

The server requires no write permissions for FinOps queries.

## Configure the Azure MCP passthrough

```yaml
providers:
  azure:
    enabled: true
    command: "npx"
    args: ["-y", "@azure/mcp@2.0.4", "server", "start"]
```

Node.js/npm must be installed for this optional passthrough. The explicit
`server start` subcommands are required; omitting them makes the CLI print help
to stdout instead of speaking MCP over stdio.

## Troubleshooting

- `401` or `403`: verify `az login`, the selected subscription, tenant, and
  Cost Management permissions.
- `0xC00000FD` on Windows: use the repository-pinned `@azure/mcp@2.0.4` and
  avoid overriding it with `latest` until the newer version is validated.
- JSON parse errors during startup: confirm the command includes `server
  start` and that no wrapper writes diagnostic text to stdout.

## Official references

- [Azure MCP Server concepts](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/concepts)
- [Azure MCP Server tools and authentication](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/)
