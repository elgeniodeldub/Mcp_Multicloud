# â˜ï¸ Multicloud MCP Server

> **Unifica los servidores MCP oficiales de AWS y Azure bajo un Ãºnico endpoint con namespace inteligente, herramientas multicloud nativas y arquitectura stateless lista para producciÃ³n.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP 2026-07-28](https://img.shields.io/badge/MCP-2026--07--28-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-Apache%202.0-orange.svg)](LICENSE)

## ðŸŽ¯ QuÃ© es esto

El **Multicloud MCP Server** es un servidor MCP de tipo **Proxy Aggregator** que actÃºa como fachada unificada sobre los servidores MCP oficiales de **AWS** (`awslabs/mcp`) y **Azure** (`microsoft/mcp`).

En lugar de configurar docenas de conexiones MCP individuales en tu IDE o agente, conectas **un solo servidor** que expone todas las capacidades de ambas nubes con:

- ðŸ”€ **Namespace inteligente**: `aws__eks__describe_cluster`, `azure__aks__get_credentials`
- ðŸ›¡ï¸ **Aislamiento de fallos**: si un provider falla, los demÃ¡s siguen funcionando
- ðŸ“Š **Herramientas multicloud nativas**: comparaciÃ³n de costos, migraciÃ³n de recursos, validaciÃ³n cross-cloud
- âš¡ **Arquitectura stateless** (MCP 2026-07-28): escalable horizontalmente sin sesiones persistentes
- ðŸ” **AutenticaciÃ³n unificada** con soporte para mÃºltiples credenciales por provider

## ðŸš€ InstalaciÃ³n

```bash
# Con uv (recomendado)
uv tool install multicloud-mcp-server

# Con pip
pip install multicloud-mcp-server
```

## âš™ï¸ ConfiguraciÃ³n rÃ¡pida

```bash
export AWS_REGION=us-east-1
export AZURE_SUBSCRIPTION_ID=your-sub-id
multicloud-mcp-server
```

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

## ðŸ› ï¸ Herramientas Disponibles

### AWS (`aws__*`)
Todas las herramientas del servidor MCP oficial de AWS con prefijo `aws__`.

### Azure (`azure__*`)
Todas las herramientas del servidor MCP oficial de Azure con prefijo `azure__`.

### Multicloud nativas (`multicloud__*`)

| Tool | DescripciÃ³n |
|------|-------------|
| `multicloud__compare_cost` | Compara costos AWS vs Azure |
| `multicloud__map_resource` | Mapea recursos entre nubes |
| `multicloud__list_providers` | Lista providers y su estado |
| `multicloud__discover_resources` | Descubre recursos en todas las nubes |
| `multicloud__security_posture` | Analiza postura de seguridad cross-cloud |
| `multicloud__compliance_check` | Verifica compliance CIS/NIST |

## ðŸ“– DocumentaciÃ³n

- [Arquitectura](docs/architecture.md)
- [ConfiguraciÃ³n](docs/configuration.md)
- [Contribuir](docs/contributing.md)

## ðŸ“„ Licencia

Apache 2.0 â€” ver [LICENSE](LICENSE).
