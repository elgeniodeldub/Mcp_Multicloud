# ConfiguraciÃ³n del Multicloud MCP Server

## MÃ©todos de ConfiguraciÃ³n

1. **Variables de entorno** (mayor prioridad)
2. **Archivo YAML** (especificado o por defecto)
3. **Valores por defecto** (menor prioridad)

## Archivo de ConfiguraciÃ³n

### Ubicaciones por defecto

- `MULTICLOUD_CONFIG_PATH`
- `./config.yaml`
- `./config.yml`
- `/etc/multicloud-mcp/config.yaml`

### Variables de Entorno

Todas usan el prefijo `MULTICLOUD_`:

| Variable | DescripciÃ³n | Ejemplo |
|----------|-------------|---------|
| `MULTICLOUD_CONFIG_PATH` | Ruta al archivo YAML | `/etc/mcp/config.yaml` |
| `MULTICLOUD_LOG_LEVEL` | Nivel de logging | `DEBUG` |
| `MULTICLOUD_SERVER__TRANSPORT` | Transporte | `http` |
| `MULTICLOUD_SERVER__HTTP__PORT` | Puerto HTTP | `8080` |

> **Nota**: El separador `__` navega objetos anidados.

## ConfiguraciÃ³n por Cliente

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "multicloud": {
      "command": "uvx",
      "args": ["multicloud-mcp-server@latest"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AZURE_SUBSCRIPTION_ID": "your-sub-id"
      }
    }
  }
}
```
