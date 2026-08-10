# Capabilities y dominio canónico

El router mantiene el passthrough de tools MCP con namespaces, mientras que la
capa multicloud usa capabilities semánticas: `compute`, `storage`, `database`,
`kubernetes`, `cost` y `security`.

AWS y Azure declaran sus mappings internos. Las tools de aplicación no dependen
de nombres upstream como EC2, EKS o AKS. Los modelos provider-independent viven
en `multicloud_mcp.domain` e incluyen recursos, costos con `Decimal`, findings
de seguridad y estados normalizados. Las monedas se mantienen separadas.

Los adapters MCP comparten `StdioMCPTransport`, timeout, reintentos para errores
transitorios, semáforo de concurrencia y circuit breaker. Una falla de un
proveedor se reporta de forma aislada y no requiere detener el servidor.
