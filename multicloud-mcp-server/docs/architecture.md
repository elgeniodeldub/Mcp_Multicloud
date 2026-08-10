# Arquitectura

El servidor implementa el patrón Proxy Aggregator para unificar los servidores MCP de AWS y Azure.

## Flujo

```text
Cliente MCP → transporte stdio/HTTP → servidor MCP → router → adaptador AWS/Azure
                                          ↓
                              tools multicloud nativas
```

El router conserva un catálogo con TTL, aplica namespaces (`aws__`, `azure__`) y usa circuit breakers y health checks por proveedor.

## Seguridad HTTP

El transporte HTTP se crea mediante una capa separada que aplica, antes de ejecutar una tool:

- request ID y headers de seguridad;
- Bearer API key opcional para `/mcp`;
- protección configurable de `/metrics` y `/health` público;
- CORS explícito, nunca wildcard automático;
- límite de cuerpo y rate limiting por IP;
- política central `allow_all` o `read_only`;
- auditoría sin tokens, credenciales ni argumentos sensibles.

El transporte `stdio` no requiere autenticación HTTP y mantiene el flujo existente. Para producción HTTP se recomienda terminar TLS en un reverse proxy, ingress, API gateway o load balancer.

## Costos reales

`finops__get_actual_costs` consulta AWS Cost Explorer (`UnblendedCost`) y Azure Cost Management (`PreTaxCost`). El MCP no calcula ni hardcodea precios; devuelve los resultados separados por proveedor porque las métricas no se homologan automáticamente.
