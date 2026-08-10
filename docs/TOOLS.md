# MCP Tools

## Tool categories

The server exposes two tool families.

### Provider-native tools

Provider-native tools come from the AWS/Azure adapters and are discovered dynamically through the provider router.

They should retain provider-specific semantics and naming.

### Multicloud-native tools

These tools live in `src/multicloud_mcp/tools/` and implement cross-provider behavior.

## Native tool catalog

### `CostComparisonTool`

**Module:** `tools/cost_comparison.py`

Purpose:

- compare cost/resource information across cloud providers;
- provide a common multicloud entry point above provider billing implementations.

Confirmed server tool name:

```text
multicloud__compare_cost
```

### `ResourceMapperTool`

**Module:** `tools/resource_mapper.py`

Purpose:

- translate provider-specific resource shapes into a common model;
- support cross-cloud resource comparison and aggregation.

### `ListProvidersTool`

**Module:** `tools/list_providers.py`

Purpose:

- list providers known to the router/server;
- expose provider availability/health context to MCP consumers.

### `DiscoverResourcesTool`

**Module:** `tools/discover_resources.py`

Purpose:

- discover resources across configured providers;
- provide one entry point for multicloud inventory workflows.

### `SecurityPostureTool`

**Module:** `tools/security_posture.py`

Purpose:

- execute/aggregate provider security posture operations;
- return a multicloud security-oriented result.

The tool receives the router so it can work against configured providers rather than relying on one cloud implementation.

### `ComplianceCheckerTool`

**Module:** `tools/compliance.py`

Purpose:

- execute compliance-oriented checks across providers;
- aggregate results into a multicloud response.

The tool also uses the router for provider access.

## Tool registration

Native tools are registered centrally by `MulticloudMCPServer._get_multicloud_tools()`.

Native tool calls are dispatched by `_call_multicloud_tool(...)`.

Provider-native tool calls are delegated to `ProviderRouter`.

## Error behavior

Provider errors should be normalized at the routing/native tool boundaries. Provider failures should not leak implementation-specific exceptions directly to MCP clients where they can be converted into an actionable MCP error response instead.

Typical error categories:

- tool not found;
- provider unavailable;
- provider timeout;
- invalid tool arguments;
- provider execution failure;
- incomplete cross-cloud result because one provider is unhealthy.

## Documentation rule for future tools

Every new tool should document:

- MCP name;
- description;
- input schema;
- output contract;
- providers used;
- required permissions;
- failure behavior;
- at least one example call/result.

The exact MCP names and input schemas should be copied from the tool class implementation to avoid documentation drift.
