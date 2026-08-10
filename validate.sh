#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# validate.sh — Script de validación para el Multicloud MCP Server
# Uso: bash validate.sh [--strict]
#   --strict: falla si hay warnings además de errores
# ============================================================

STRICT=false
if [[ "${1:-}" == "--strict" ]]; then
    STRICT=true
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0
PASS=0

log_info() { echo -e "${BLUE}ℹ${NC}  $1"; }
log_pass() { echo -e "${GREEN}✅${NC} $1"; ((PASS++)); }
log_warn() { echo -e "${YELLOW}⚠${NC}  $1"; ((WARNINGS++)); }
log_fail() { echo -e "${RED}❌${NC} $1"; ((ERRORS++)); }

separator() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

separator
echo -e "${BLUE}🔍 Validación del Multicloud MCP Server${NC}"
separator

# ─────────────────────────────────────────────────────────────
# 1. Verificar estructura de archivos
# ─────────────────────────────────────────────────────────────
log_info "Verificando estructura de archivos..."

REQUIRED_FILES=(
    "pyproject.toml"
    "src/multicloud_mcp/__init__.py"
    "src/multicloud_mcp/server.py"
    "src/multicloud_mcp/config.py"
    "src/multicloud_mcp/router.py"
    "src/multicloud_mcp/health.py"
    "src/multicloud_mcp/cache.py"
    "src/multicloud_mcp/providers/base.py"
    "src/multicloud_mcp/providers/aws.py"
    "src/multicloud_mcp/providers/azure.py"
    "src/multicloud_mcp/tools/cost_comparison.py"
    "src/multicloud_mcp/tools/resource_mapper.py"
    "src/multicloud_mcp/tools/list_providers.py"
    "src/multicloud_mcp/tools/discover_resources.py"
    "src/multicloud_mcp/tools/security_posture.py"
    "src/multicloud_mcp/tools/compliance.py"
    "tests/__init__.py"
    "tests/test_router.py"
    "tests/test_providers.py"
    "tests/test_multicloud_tools.py"
    "tests/integration/__init__.py"
    "tests/integration/test_end_to_end.py"
    "Dockerfile"
    "Makefile"
    "config.yaml"
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    ".gitignore"
    ".pre-commit-config.yaml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        log_pass "Existe: $file"
    else
        log_fail "Falta: $file"
    fi
done

# ─────────────────────────────────────────────────────────────
# 2. Verificar Python disponible
# ─────────────────────────────────────────────────────────────
separator
log_info "Verificando entorno Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    log_pass "Python encontrado: $PYTHON_VERSION"
else
    log_fail "Python 3 no encontrado"
fi

if command -v uv &> /dev/null; then
    log_pass "uv encontrado"
else
    log_warn "uv no encontrado (recomendado para instalación rápida)"
fi

# ─────────────────────────────────────────────────────────────
# 3. Verificar dependencias instaladas
# ─────────────────────────────────────────────────────────────
separator
log_info "Verificando dependencias..."

python3 -c "import mcp" 2>/dev/null && log_pass "mcp SDK instalado" || log_fail "mcp SDK no instalado"
python3 -c "import pydantic" 2>/dev/null && log_pass "pydantic instalado" || log_fail "pydantic no instalado"
python3 -c "import structlog" 2>/dev/null && log_pass "structlog instalado" || log_fail "structlog no instalado"
python3 -c "import starlette" 2>/dev/null && log_pass "starlette instalado" || log_fail "starlette no instalado"
python3 -c "import uvicorn" 2>/dev/null && log_pass "uvicorn instalado" || log_fail "uvicorn no instalado"
python3 -c "import yaml" 2>/dev/null && log_pass "pyyaml instalado" || log_fail "pyyaml no instalado"
python3 -c "import tenacity" 2>/dev/null && log_pass "tenacity instalado" || log_fail "tenacity no instalado"

# ─────────────────────────────────────────────────────────────
# 4. Linting con ruff
# ─────────────────────────────────────────────────────────────
separator
log_info "Ejecutando ruff (lint)..."

if command -v ruff &> /dev/null; then
    if ruff check src tests 2>/dev/null; then
        log_pass "ruff check: sin errores"
    else
        log_fail "ruff check: encontró errores"
    fi
else
    log_warn "ruff no instalado, saltando lint"
fi

# ─────────────────────────────────────────────────────────────
# 5. Formato con ruff
# ─────────────────────────────────────────────────────────────
log_info "Verificando formato con ruff..."

if command -v ruff &> /dev/null; then
    if ruff format --check src tests 2>/dev/null; then
        log_pass "ruff format: código formateado correctamente"
    else
        log_warn "ruff format: código no formateado (ejecutar 'ruff format src tests')"
    fi
else
    log_warn "ruff no instalado, saltando formato"
fi

# ─────────────────────────────────────────────────────────────
# 6. Type checking con mypy
# ─────────────────────────────────────────────────────────────
separator
log_info "Ejecutando mypy (type checking)..."

if command -v mypy &> /dev/null; then
    if mypy src 2>/dev/null; then
        log_pass "mypy: sin errores de tipo"
    else
        log_fail "mypy: encontró errores de tipo"
    fi
else
    log_warn "mypy no instalado, saltando type check"
fi

# ─────────────────────────────────────────────────────────────
# 7. Tests unitarios
# ─────────────────────────────────────────────────────────────
separator
log_info "Ejecutando tests con pytest..."

if command -v pytest &> /dev/null; then
    if pytest -v tests/ 2>/dev/null; then
        log_pass "pytest: todos los tests pasan"
    else
        log_fail "pytest: algunos tests fallaron"
    fi
else
    log_warn "pytest no instalado, saltando tests"
fi

# ─────────────────────────────────────────────────────────────
# 8. Verificar STUBs implementados
# ─────────────────────────────────────────────────────────────
separator
log_info "Verificando implementación de STUBs..."

STUB_FILES=(
    "src/multicloud_mcp/tools/list_providers.py"
    "src/multicloud_mcp/tools/discover_resources.py"
    "src/multicloud_mcp/tools/security_posture.py"
    "src/multicloud_mcp/tools/compliance.py"
    "tests/integration/test_end_to_end.py"
)

for file in "${STUB_FILES[@]}"; do
    if grep -q "NotImplementedError" "$file" 2>/dev/null; then
        log_warn "STUB pendiente: $file (contiene NotImplementedError)"
    else
        log_pass "Implementado: $file"
    fi
done

# ─────────────────────────────────────────────────────────────
# 9. Verificar imports circulares
# ─────────────────────────────────────────────────────────────
separator
log_info "Verificando imports..."

if python3 -c "from multicloud_mcp.server import main; from multicloud_mcp.config import Settings; from multicloud_mcp.router import ProviderRouter; from multicloud_mcp.health import HealthMonitor; from multicloud_mcp.cache import ToolsCache; print('OK')" 2>/dev/null; then
    log_pass "Imports principales: OK"
else
    log_fail "Imports principales: ERROR (posible import circular)"
fi

# ─────────────────────────────────────────────────────────────
# 10. Verificar Docker
# ─────────────────────────────────────────────────────────────
separator
log_info "Verificando Docker..."

if command -v docker &> /dev/null; then
    if docker build -t multicloud-mcp-server:validate . 2>/dev/null; then
        log_pass "Docker build: exitoso"
        docker rmi multicloud-mcp-server:validate 2>/dev/null || true
    else
        log_fail "Docker build: falló"
    fi
else
    log_warn "Docker no encontrado, saltando"
fi

# ─────────────────────────────────────────────────────────────
# 11. Verificar config.yaml válido
# ─────────────────────────────────────────────────────────────
separator
log_info "Verificando config.yaml..."

if python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" 2>/dev/null; then
    log_pass "config.yaml: YAML válido"
else
    log_fail "config.yaml: YAML inválido"
fi

# ─────────────────────────────────────────────────────────────
# Resumen
# ─────────────────────────────────────────────────────────────
separator
echo -e "${BLUE}📊 Resumen de Validación${NC}"
separator
echo -e "${GREEN}✅ Pasaron:${NC}    $PASS"
echo -e "${YELLOW}⚠️  Warnings:${NC}  $WARNINGS"
echo -e "${RED}❌ Errores:${NC}   $ERRORS"
separator

if [[ $ERRORS -eq 0 ]]; then
    if [[ "$STRICT" == "true" && $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Modo estricto: hay warnings, considera corregirlos.${NC}"
        exit 1
    fi
    echo -e "${GREEN}🎉 ¡Validación exitosa! El proyecto está listo.${NC}"
    exit 0
else
    echo -e "${RED}💥 Validación fallida. Corrige los errores marcados arriba.${NC}"
    exit 1
fi
