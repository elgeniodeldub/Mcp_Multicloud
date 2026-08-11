# Configuración

La configuración se carga, por orden de prioridad, desde variables de entorno, un archivo YAML (`MULTICLOUD_CONFIG_PATH`, `./config.yaml` o `./config.yml`) y valores predeterminados.

Las variables anidadas usan `__`, por ejemplo `MULTICLOUD_SERVER__TRANSPORT=http` y `MULTICLOUD_SERVER__HTTP__PORT=8080`.

## Seguridad HTTP

El host HTTP predeterminado es `127.0.0.1`. Para un despliegue seguro usa `examples/config.secure.yaml` y define el secreto fuera de YAML:

```powershell
$env:MULTICLOUD_API_KEY = "super-secret-token"
multicloud-mcp-server --config examples/config.secure.yaml
```

Las opciones principales son:

- `security.authentication`: Bearer API key y protección de `/metrics`.
- `security.cors`: CORS explícito; está deshabilitado por defecto.
- `security.max_request_size_bytes`: límite de cuerpo de `/mcp`, 1 MiB por defecto.
- `security.rate_limit`: límite por IP en memoria, 60 solicitudes por minuto por defecto.
- `security.tool_policy`: `allow_all` o `read_only`.

## AWS provider passthrough

El `awslabs.core-mcp-server` externo queda deshabilitado en el `config.yaml`
predeterminado porque su resolución actual no es compatible de forma confiable
con la versión del SDK MCP usada por este proyecto.

Esto no deshabilita FinOps nativo de AWS. Las herramientas
`finops__get_actual_costs`, `finops__get_cost`, `finops__breakdown` y
`finops__compare` continúan usando AWS Cost Explorer mediante `boto3`.

Para habilitar `aws__*`, instala y valida explícitamente un servidor AWS MCP
compatible y sobrescribe la configuración:

```yaml
providers:
  aws:
    enabled: true
    command: "<validated-command>"
    args: ["<validated-aws-mcp-server>"]
```

No reactives el paquete externo predeterminado sin verificar primero su
compatibilidad con el protocolo MCP y las dependencias actuales.

`stdio` continúa funcionando sin autenticación HTTP. Consulta [Seguridad HTTP](security.md) para TLS, auditoría, métricas y reverse proxies.
