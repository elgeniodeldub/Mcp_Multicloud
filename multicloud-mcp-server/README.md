# Multicloud MCP Server

Servidor MCP unificado para AWS y Azure con namespaces por proveedor, herramientas multicloud y transporte `stdio` o HTTP.

## Instalación

```bash
pip install multicloud-mcp-server
multicloud-mcp-server
```

## HTTP seguro

El HTTP escucha en `127.0.0.1` por defecto. Para una configuración de producción usa `examples/config.secure.yaml`:

```powershell
$env:MULTICLOUD_API_KEY = "super-secret-token"
multicloud-mcp-server --config examples/config.secure.yaml
```

No expongas el servidor HTTP directamente a Internet. Usa autenticación, TLS y controles de red apropiados. Consulta [Seguridad HTTP](docs/security.md).

## Herramientas

| Tool | Descripción |
|------|-------------|
| `finops__get_actual_costs` | Costos reales no amortizados de AWS Cost Explorer y Azure Cost Management |
| `multicloud__map_resource` | Mapeo de recursos entre nubes |
| `multicloud__list_providers` | Estado de los providers |
| `multicloud__discover_resources` | Descubrimiento cross-cloud |
| `multicloud__security_posture` | Análisis de seguridad |
| `multicloud__compliance_check` | Validación CIS/NIST |

Las herramientas nativas de AWS y Azure conservan sus namespaces (`aws__*` y `azure__*`).

## Documentación

- [Arquitectura](docs/architecture.md)
- [Configuración](docs/configuration.md)
- [Seguridad HTTP](docs/security.md)
- [Contribuir](docs/contributing.md)

Licencia Apache 2.0.
