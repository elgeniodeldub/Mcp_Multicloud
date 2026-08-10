# Contribuir al Multicloud MCP Server

## CÃ³mo Contribuir

### Reportar Bugs

1. Verifica que no estÃ© ya reportado en Issues
2. Abre un nuevo issue con pasos para reproducir

### Pull Requests

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nombre-descriptivo`
3. Commits con [Conventional Commits](https://www.conventionalcommits.org/)
4. AsegÃºrate de que `make check` pasa
5. Abre el PR

## Entorno de Desarrollo

```bash
uv pip install -e ".[dev]"
pre-commit install
pytest
```

## Agregar un Nuevo Provider

Crear `src/multicloud_mcp/providers/<nombre>.py` heredando de `ProviderAdapter`, luego registrar en `server.py`.
