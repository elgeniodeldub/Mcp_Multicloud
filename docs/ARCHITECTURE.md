# Architecture

## Overview

Multicloud MCP Server is an orchestration layer between MCP clients and cloud-specific providers. It keeps provider-specific integrations isolated behind adapters and implements cross-cloud behavior in native multicloud tools.

## Design goals

1. **Provider independence** — AWS, Azure, and future providers implement a common contract.
2. **No unnecessary duplication** — provider-native APIs/tools remain inside their provider adapters.
3. **Cross-cloud normalization** — resource/cost/security data can be combined above the provider layer.
4. **Failure isolation** — one unhealthy provider should not make the complete server unusable.
5. **MCP-native interface** — tools are discoverable and callable through MCP.
6. **Transport flexibility** — support local `stdio` and network HTTP use cases.

## Main components

### `server.py`

Primary application entry point.

Responsibilities:

- instantiate the MCP `Server`;
- register MCP `list_tools` and `call_tool` handlers;
- expose native multicloud tools;
- initialize configured providers;
- connect the provider router;
- initialize health monitoring;
- run stdio or HTTP transport;
- perform graceful shutdown.

### `router.py`

`ProviderRouter` is the provider orchestration layer.

Responsibilities:

- maintain registered providers;
- discover provider tools;
- build a tool index;
- route provider tool calls;
- aggregate provider health information;
- apply timeout/error handling around provider operations.

### `providers/base.py`

Defines the provider contract and shared data structures such as provider health and tool information.

The provider abstraction allows the server and native tools to operate without depending directly on AWS- or Azure-specific implementations.

### `providers/aws.py`

AWS adapter.

Expected responsibilities from the common contract:

- connect/initialize the underlying AWS integration;
- list provider tools;
- call provider tools;
- expose health information;
- respect configured timeout behavior.

### `providers/azure.py`

Azure adapter with the same architectural responsibilities as the AWS adapter.

### `health.py`

Provider health monitoring and circuit breaker.

Conceptually:

```text
CLOSED
  |
  | repeated failures
  v
OPEN
  |
  | recovery timeout / retry
  v
HALF_OPEN
  | success       | failure
  v               v
CLOSED           OPEN
```

This protects the MCP layer from repeatedly calling a provider that is known to be unhealthy.

### `cache.py`

Cache abstraction for repeated server/provider operations.

### `config.py`

Configuration model and loader.

Confirmed behavior includes:

- Pydantic-based settings/models;
- YAML loading;
- environment-variable resolution;
- `Settings.from_yaml(...)`;
- `Settings.load()`;
- `MULTICLOUD_CONFIG_PATH` support.

### Native tools

Located under `src/multicloud_mcp/tools/`.

These implement features that logically belong to the multicloud layer rather than a single cloud provider.

## Request flow

### Tool discovery

```text
MCP client
   |
 tools/list
   |
MulticloudMCPServer
   |
   +--> native multicloud tool definitions
   |
   +--> ProviderRouter
          |
          +--> AWS.list_tools()
          +--> Azure.list_tools()
          +--> future providers
   |
combined MCP tool list
```

### Provider-native call

```text
MCP client
   |
 tools/call
   |
MulticloudMCPServer
   |
ProviderRouter
   |
resolve tool -> provider
   |
provider.call_tool(...)
   |
provider result
```

### Multicloud-native call

```text
MCP client
   |
 tools/call
   |
MulticloudMCPServer
   |
multicloud tool
   |
ProviderRouter / normalized data
   |
AWS + Azure
   |
normalized/aggregated result
```

## Namespace strategy

Provider tools should remain uniquely namespaced so tools from different providers cannot collide. Native cross-cloud tools use a `multicloud__...` namespace.

This namespace boundary also makes the execution model clear to an MCP client:

- provider namespace -> provider-specific operation;
- `multicloud__` -> cross-provider/native operation.

## Adding a provider

A new provider should be introduced as an adapter, not by adding provider-specific conditions throughout the server.

Recommended sequence:

1. create `providers/<provider>.py`;
2. implement the provider base contract;
3. implement initialization/cleanup;
4. implement `list_tools()`;
5. implement `call_tool()`;
6. implement health checking;
7. register it in server initialization;
8. add unit tests;
9. add an integration mock;
10. update normalized resource mappings.

## Adding a native multicloud tool

1. add a module under `tools/`;
2. define its MCP schema/definition;
3. implement execution against the router/providers;
4. register it in `_get_multicloud_tools()`;
5. route it in `_call_multicloud_tool()`;
6. add tests in `test_multicloud_tools.py`;
7. document it in `docs/TOOLS.md`.

## Dependency direction

Preferred dependency flow:

```text
server
  -> router
      -> provider interface
          -> provider adapters

server
  -> native tools
      -> router/provider abstractions

provider adapters
  X-> native tools
```

Native tools should depend on abstractions rather than reaching into provider implementation details whenever possible.
