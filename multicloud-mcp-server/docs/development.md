# Desarrollo y CI

## Entorno local

El proyecto requiere Python 3.11 o superior. Instala las herramientas de desarrollo desde este directorio:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy --strict src
python -m build
```

La CI ejecuta esas comprobaciones para Python 3.11, 3.12 y 3.13. También audita dependencias con `pip-audit`, busca secretos con Gitleaks y escanea la imagen Docker con Trivy.

## Actualizar acciones fijadas

Las acciones se referencian por SHA completo, con la versión humana en un comentario. Para actualizar una acción, revisa la release oficial, verifica que el SHA corresponda a esa release y actualiza también Dependabot. No reemplaces el SHA por un tag mutable.

## Dependencias y reproducibilidad

Las dependencias runtime están separadas de las herramientas `dev` en `pyproject.toml`. Cada cambio debe justificar su impacto y ejecutar `pip-audit`. En entornos donde se use `uv`, mantén un `uv.lock` revisado y ejecuta `uv sync --frozen`; nunca regeneres el lock silenciosamente en CI.
