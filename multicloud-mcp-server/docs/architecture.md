# Arquitectura del Multicloud MCP Server

## VisiÃ³n General

El Multicloud MCP Server implementa el patrÃ³n **Proxy Aggregator** sobre el protocolo MCP (Model Context Protocol), actuando como fachada unificada para mÃºltiples servidores MCP de nube.

## Diagrama de Componentes

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                      MCP CLIENT                              â”‚
â”‚         (Claude Desktop, Cursor, VS Code, etc.)             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚ stdio / HTTP (stateless)
                           â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              MULTICLOUD MCP SERVER                           â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚  â”‚   Server    â”‚  â”‚   Router    â”‚  â”‚  Health Monitor     â”‚ â”‚
â”‚  â”‚  (FastMCP)  â”‚  â”‚  + Cache    â”‚  â”‚  + Circuit Breaker  â”‚ â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â”‚         â”‚                â”‚                                   â”‚
â”‚    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”                            â”‚
â”‚    â”‚  AWS    â”‚      â”‚  Azure  â”‚      [GCP, OCI, ...]       â”‚
â”‚    â”‚ Adapter â”‚      â”‚ Adapter â”‚                            â”‚
â”‚    â”‚ (stdio) â”‚      â”‚ (stdio) â”‚                            â”‚
â”‚    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜                            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
          â”‚                â”‚
          â–¼                â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  AWS MCP Server â”‚  â”‚ Azure MCP Serverâ”‚
â”‚  (awslabs/mcp)  â”‚  â”‚ (microsoft/mcp) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Patrones de DiseÃ±o

### 1. Proxy Aggregator

El servidor actÃºa como proxy que agrega mÃºltiples servidores MCP upstream. Cada tool se expone con un namespace Ãºnico: `provider__tool_name`.

### 2. Circuit Breaker

Cada provider tiene un circuit breaker que:
- Cierra el circuito tras N fallos consecutivos
- Rechaza llamadas durante el estado OPEN
- Prueba recuperaciÃ³n con HALF_OPEN

### 3. Cache con TTL

El catÃ¡logo de tools se cachea por 5 minutos.

## Flujo de Datos

### Listado de Tools

1. Cliente envÃ­a `tools/list`
2. Server verifica cache (TTL 5min)
3. Si expirado: paraleliza `list_tools()` a todos los providers
4. Aplica namespace: `aws__` + nombre_original
5. Agrega tools multicloud nativas
6. Retorna catÃ¡logo unificado

### EjecuciÃ³n de Tool

1. Cliente envÃ­a `tools/call` con `aws__s3__list_buckets`
2. Router.parse() -> provider="aws", tool="s3__list_buckets"
3. Verifica circuit breaker del provider
4. Ejecuta `call_tool()` en AWSProvider
5. AWSProvider traduce a nombre original y llama upstream
6. Resultado fluye de vuelta al cliente
