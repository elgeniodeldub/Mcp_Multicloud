# Architecture

## Overview

Multicloud MCP Server is a gateway/aggregator for AWS and Azure provider-native MCP capabilities plus native cross-cloud tools.

```text
User
 |
LLM / MCP Client
 |
MulticloudMCPServer
 |
 +--> Security policy
 +--> Native tools (FinOps, discovery, mapping, security, compliance)
 +--> ProviderRouter
       +--> AWSProvider
       +--> AzureProvider
```

## LLM responsibility

The server does not require an internal LLM. The upstream model/client understands intent, chooses tools, builds arguments, and interprets results. The MCP server exposes capabilities, applies policy, routes calls, invokes providers, and returns structured data.

## Namespaces

```text
aws__*
azure__*
multicloud__*
finops__*
```

## Security boundary

HTTP mode should be treated as a privileged gateway to cloud capabilities. The internal policy layer provides defense in depth; AWS IAM and Azure RBAC remain provider authorization boundaries.

## Extension model

To add a provider: implement the provider contract, add connection/discovery/invocation, register it, add health handling/tests, and extend native normalization only where useful.
