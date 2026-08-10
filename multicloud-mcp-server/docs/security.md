# Seguridad HTTP

El servidor trata el transporte HTTP como un gateway privilegiado hacia AWS y Azure.

> El servidor HTTP integrado no debe exponerse directamente a Internet sin autenticación, terminación TLS y controles de red apropiados.

## Configuración segura

Usa `examples/config.secure.yaml` y define el secreto fuera de YAML:

```powershell
$env:MULTICLOUD_API_KEY = "super-secret-token"
multicloud-mcp-server --config examples/config.secure.yaml
```

`/mcp` requiere `Authorization: Bearer <token>`. El token se obtiene únicamente de la variable indicada por `api_key_env` y nunca se registra.

`/health` permanece público para probes de Kubernetes, Docker y balanceadores. `/metrics` requiere autenticación por defecto y puede hacerse público con `protect_metrics: false`.

## Protecciones HTTP

- CORS está deshabilitado por defecto y no usa orígenes wildcard.
- El límite de cuerpo de `/mcp` es 1 MiB por defecto.
- El rate limiter en memoria limita por IP y es apropiado para una sola instancia.
- Se envían `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control: no-store` y `X-Request-ID`.
- Los errores inesperados responden `Internal server error`; el detalle solo queda en logs internos.

Para varias réplicas, usa un API gateway, reverse proxy o limitador distribuido. Termina TLS en el reverse proxy, ingress, API gateway o load balancer; el servidor no activa HSTS porque no sabe si la conexión externa usa HTTPS.

## Política de herramientas

`allow_all` mantiene compatibilidad hacia atrás. `read_only` bloquea nombres de tools provider-native que contienen verbos mutantes como `delete`, `terminate`, `update`, `restart`, `deploy` o `execute`. Las herramientas nativas `finops__*` y `multicloud__*` permanecen permitidas.

La política no sustituye IAM/RBAC del proveedor. Debe combinarse con credenciales de mínimo privilegio.

## Auditoría y métricas

Cada invocación HTTP registra request ID, tool, provider, IP, resultado, duración y política. No se registran headers de autorización, credenciales ni argumentos sensibles. Los contadores Prometheus no usan request ID, IP, account ID, subscription ID ni resource ID como labels.

## Supply chain y releases

La CI ejecuta tests, cobertura, Ruff, mypy estricto, build de paquete, `pip-audit`, Gitleaks y Trivy. CodeQL analiza Python en cada cambio relevante y semanalmente. Dependabot revisa semanalmente PyPI, Docker y GitHub Actions.

Las dependencias de los proveedores MCP del ejemplo están fijadas a versiones concretas; evita `@latest` en despliegues. La imagen Docker usa un builder separado y el runtime conserva únicamente lo necesario, ejecutando como `mcp` sin privilegios.

Cada release SemVer genera wheel, sdist, SBOM CycloneDX del entorno Python, SBOM SPDX de la imagen y `SHA256SUMS`. GitHub Artifact Attestations permiten verificar la procedencia con el repositorio, commit y workflow.

El workflow de release no publica automáticamente en PyPI ni en un registry de contenedores. Si se habilita esa publicación, debe hacerse en un entorno protegido con OIDC, permisos mínimos y revisión humana. La protección de ramas y Private Vulnerability Reporting deben habilitarse en la configuración del repositorio.

## Docker

El contenedor conserva el usuario no root `mcp`. El healthcheck real solo consulta `/health` cuando `MULTICLOUD_TRANSPORT=http`; el modo stdio no tiene un endpoint HTTP que monitorizar. Para despliegues externos configura explícitamente `server.http.host: 0.0.0.0` y coloca TLS y controles de red delante del contenedor.
