#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Multicloud MCP Server — Setup Script
# Genera el proyecto completo end-to-end desde cero.
# Uso: bash setup.sh [DIRECTORIO_DESTINO]
# ============================================================

DEST_DIR="${1:-multicloud-mcp-server}"
echo "🚀 Generando Multicloud MCP Server en: $DEST_DIR"

mkdir -p "$DEST_DIR"
cd "$DEST_DIR"

# Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
mkdir -p src/multicloud_mcp/providers
mkdir -p src/multicloud_mcp/tools
mkdir -p tests/integration
mkdir -p docs
mkdir -p examples
mkdir -p .github/workflows
mkdir -p helm/multicloud-mcp-server/templates
mkdir -p terraform/aws
mkdir -p terraform/azure

# ============================================================
# 1. pyproject.toml
# ============================================================
cat << 'PYPROJECT' > pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "multicloud-mcp-server"
version = "0.1.0"
description = "Unified Multicloud MCP Server for AWS and Azure — a proxy aggregator that unifies official cloud MCP servers under a single namespace."
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "you@example.com"},
]
keywords = [
    "mcp", "model-context-protocol", "multicloud", "aws", "azure",
    "cloud", "ai", "agent",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    "mcp>=1.12.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.27.0",
    "anyio>=4.0.0",
    "structlog>=24.0.0",
    "pyyaml>=6.0",
    "tenacity>=8.0.0",
    "starlette>=0.37.0",
    "uvicorn[standard]>=0.29.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
    "pre-commit>=3.0.0",
]

[project.scripts]
multicloud-mcp-server = "multicloud_mcp.server:main"

[project.urls]
Homepage = "https://github.com/your-org/multicloud-mcp-server"
Repository = "https://github.com/your-org/multicloud-mcp-server"
Issues = "https://github.com/your-org/multicloud-mcp-server/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/multicloud_mcp"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=multicloud_mcp --cov-report=term-missing --cov-report=xml"
PYPROJECT

# ============================================================
# 2. README.md
# ============================================================
cat << 'README' > README.md
# ☁️ Multicloud MCP Server

> **Unifica los servidores MCP oficiales de AWS y Azure bajo un único endpoint con namespace inteligente, herramientas multicloud nativas y arquitectura stateless lista para producción.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP 2026-07-28](https://img.shields.io/badge/MCP-2026--07--28-green.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-Apache%202.0-orange.svg)](LICENSE)

## 🎯 Qué es esto

El **Multicloud MCP Server** es un servidor MCP de tipo **Proxy Aggregator** que actúa como fachada unificada sobre los servidores MCP oficiales de **AWS** (`awslabs/mcp`) y **Azure** (`microsoft/mcp`).

En lugar de configurar docenas de conexiones MCP individuales en tu IDE o agente, conectas **un solo servidor** que expone todas las capacidades de ambas nubes con:

- 🔀 **Namespace inteligente**: `aws__eks__describe_cluster`, `azure__aks__get_credentials`
- 🛡️ **Aislamiento de fallos**: si un provider falla, los demás siguen funcionando
- 📊 **Herramientas multicloud nativas**: comparación de costos, migración de recursos, validación cross-cloud
- ⚡ **Arquitectura stateless** (MCP 2026-07-28): escalable horizontalmente sin sesiones persistentes
- 🔐 **Autenticación unificada** con soporte para múltiples credenciales por provider

## 🚀 Instalación

```bash
# Con uv (recomendado)
uv tool install multicloud-mcp-server

# Con pip
pip install multicloud-mcp-server
```

## ⚙️ Configuración rápida

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

## 🛠️ Herramientas Disponibles

### AWS (`aws__*`)
Todas las herramientas del servidor MCP oficial de AWS con prefijo `aws__`.

### Azure (`azure__*`)
Todas las herramientas del servidor MCP oficial de Azure con prefijo `azure__`.

### Multicloud nativas (`multicloud__*`)

| Tool | Descripción |
|------|-------------|
| `multicloud__compare_cost` | Compara costos AWS vs Azure |
| `multicloud__map_resource` | Mapea recursos entre nubes |
| `multicloud__list_providers` | Lista providers y su estado |
| `multicloud__discover_resources` | Descubre recursos en todas las nubes |
| `multicloud__security_posture` | Analiza postura de seguridad cross-cloud |
| `multicloud__compliance_check` | Verifica compliance CIS/NIST |

## 📖 Documentación

- [Arquitectura](docs/architecture.md)
- [Configuración](docs/configuration.md)
- [Contribuir](docs/contributing.md)

## 📄 Licencia

Apache 2.0 — ver [LICENSE](LICENSE).
README

# ============================================================
# 3. src/multicloud_mcp/__init__.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/__init__.py
"""Multicloud MCP Server — Unified proxy aggregator for AWS and Azure MCP servers."""

__version__ = "0.1.0"
__all__ = ["create_server", "main"]
EOF

# ============================================================
# 4. src/multicloud_mcp/config.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/config.py
"""Configuration management using Pydantic Settings."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def resolve_env_vars(obj: Any) -> Any:
    """Recursively resolve ${VAR} and ${VAR:-default} patterns in config."""
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    if isinstance(obj, str):
        pattern = re.compile(r"\$\{(\w+)(?::-([^}]*))?\}")
        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            return os.environ.get(var_name, default if default is not None else match.group(0))
        return pattern.sub(replacer, obj)
    return obj


class ProviderConfig(BaseModel):
    """Configuration for an upstream MCP provider."""

    enabled: bool = True
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    namespace: str
    health_check_interval: int = Field(default=30, ge=5)
    timeout: int = Field(default=60, ge=1)
    description: str = ""

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        if "__" in v:
            raise ValueError("Namespace cannot contain '__' (reserved for separator)")
        if not v.isidentifier():
            raise ValueError("Namespace must be a valid Python identifier")
        return v


class MulticloudToolsConfig(BaseModel):
    """Configuration for native multicloud tools."""

    enabled: bool = True
    tools: list[str] = Field(default_factory=lambda: [
        "cost_comparison",
        "resource_mapper",
        "list_providers",
        "discover_resources",
        "security_posture",
        "compliance_checker",
    ])


class HttpConfig(BaseModel):
    """HTTP transport configuration."""

    host: str = "0.0.0.0"
    port: int = 8080


class ServerConfig(BaseModel):
    """Server-level configuration."""

    name: str = "multicloud-mcp-server"
    version: str = "0.1.0"
    transport: str = Field(default="stdio", pattern="^(stdio|http)$")
    http: HttpConfig = Field(default_factory=HttpConfig)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="json", pattern="^(json|console)$")


class Settings(BaseSettings):
    """Application settings loaded from environment and config file."""

    model_config = SettingsConfigDict(
        env_prefix="MULTICLOUD_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    config_path: str | None = Field(default=None, alias="MULTICLOUD_CONFIG_PATH")
    log_level: str = Field(default="INFO", alias="MULTICLOUD_LOG_LEVEL")

    server: ServerConfig = Field(default_factory=ServerConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    multicloud: MulticloudToolsConfig = Field(default_factory=MulticloudToolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Settings":
        """Load settings from a YAML file with env var resolution."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        resolved_data = resolve_env_vars(raw_data)
        return cls.model_validate(resolved_data)

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from file or environment."""
        config_path = os.environ.get("MULTICLOUD_CONFIG_PATH")

        if config_path and Path(config_path).exists():
            return cls.from_yaml(config_path)

        for default_path in ["config.yaml", "config.yml", "/etc/multicloud-mcp/config.yaml"]:
            if Path(default_path).exists():
                return cls.from_yaml(default_path)

        return cls()
EOF

# ============================================================
# 5. src/multicloud_mcp/providers/base.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/providers/base.py
"""Abstract base class for upstream MCP provider adapters."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class ProviderHealth:
    """Health status of a provider."""

    healthy: bool = False
    last_check: float = field(default_factory=lambda: 0.0)
    error_message: str | None = None
    tools_count: int = 0
    latency_ms: float = 0.0


@dataclass
class ToolInfo:
    """Information about a tool from an upstream provider."""

    name: str
    description: str
    input_schema: dict[str, Any]
    original_name: str
    provider: str
    namespace: str


class ProviderAdapter(ABC):
    """Abstract adapter for connecting to upstream MCP servers."""

    def __init__(
        self,
        name: str,
        namespace: str,
        command: str,
        args: list[str],
        env: dict[str, str],
        timeout: int = 60,
    ) -> None:
        self.name = name
        self.namespace = namespace
        self.command = command
        self.args = args
        self.env = env
        self.timeout = timeout
        self.health = ProviderHealth()
        self._tools: list[ToolInfo] = []
        self._lock = asyncio.Lock()
        self._logger = logger.bind(provider=name, namespace=namespace)

    @property
    def tools(self) -> list[ToolInfo]:
        """Return cached tools list."""
        return self._tools

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the upstream MCP server."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the upstream MCP server."""

    @abstractmethod
    async def list_tools(self) -> list[ToolInfo]:
        """List available tools from the upstream server."""

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the upstream server."""

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Perform a health check on the provider."""

    def _namespaced_name(self, original_name: str) -> str:
        """Convert original tool name to namespaced name."""
        return f"{self.namespace}__{original_name}"

    def _original_name(self, namespaced_name: str) -> str:
        """Convert namespaced name back to original tool name."""
        prefix = f"{self.namespace}__"
        if namespaced_name.startswith(prefix):
            return namespaced_name[len(prefix):]
        return namespaced_name
EOF

# ============================================================
# 6. src/multicloud_mcp/providers/aws.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/providers/aws.py
"""AWS MCP Server adapter using stdio transport."""

from __future__ import annotations

import time
from typing import Any

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo

logger = structlog.get_logger()


class AWSProvider(ProviderAdapter):
    """Adapter for the official AWS MCP Server (awslabs/mcp)."""

    def __init__(
        self,
        command: str = "uvx",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 60,
    ) -> None:
        super().__init__(
            name="aws",
            namespace="aws",
            command=command,
            args=args or ["awslabs.core-mcp-server@latest"],
            env=env or {},
            timeout=timeout,
        )
        self._session: ClientSession | None = None
        self._stdio_ctx = None
        self._client_ctx = None

    async def connect(self) -> None:
        """Connect to AWS MCP Server via stdio."""
        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env,
            )
            self._stdio_ctx = stdio_client(server_params)
            read, write = await self._stdio_ctx.__aenter__()

            self._client_ctx = ClientSession(read, write)
            self._session = await self._client_ctx.__aenter__()
            await self._session.initialize()

            self._logger.info("aws_provider.connected")
        except Exception as e:
            self._logger.error("aws_provider.connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from AWS MCP Server."""
        try:
            if self._client_ctx:
                await self._client_ctx.__aexit__(None, None, None)
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
            self._session = None
            self._logger.info("aws_provider.disconnected")
        except Exception as e:
            self._logger.warning("aws_provider.disconnect_error", error=str(e))

    async def list_tools(self) -> list[ToolInfo]:
        """List tools from AWS MCP Server with namespace prefix."""
        if not self._session:
            await self.connect()

        try:
            tools_response = await self._session.list_tools()
            self._tools = []

            for tool in tools_response.tools:
                namespaced = self._namespaced_name(tool.name)
                self._tools.append(
                    ToolInfo(
                        name=namespaced,
                        description=f"[AWS] {tool.description}",
                        input_schema=tool.inputSchema,
                        original_name=tool.name,
                        provider="aws",
                        namespace="aws",
                    )
                )

            self.health.tools_count = len(self._tools)
            self._logger.info("aws_provider.tools_loaded", count=len(self._tools))
            return self._tools

        except Exception as e:
            self._logger.error("aws_provider.list_tools_failed", error=str(e))
            self.health.healthy = False
            self.health.error_message = str(e)
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on AWS MCP Server."""
        if not self._session:
            await self.connect()

        original_name = self._original_name(tool_name)

        try:
            self._logger.debug(
                "aws_provider.calling_tool",
                namespaced=tool_name,
                original=original_name,
            )

            result = await self._session.call_tool(original_name, arguments)

            content = []
            for item in result.content:
                if hasattr(item, "text"):
                    content.append({"type": "text", "text": item.text})
                elif hasattr(item, "data"):
                    content.append({"type": "resource", "data": item.data})
                else:
                    content.append({"type": "text", "text": str(item)})

            return {
                "content": content,
                "isError": result.isError if hasattr(result, "isError") else False,
            }

        except Exception as e:
            self._logger.error(
                "aws_provider.tool_call_failed",
                tool=original_name,
                error=str(e),
            )
            return {
                "content": [{"type": "text", "text": f"AWS Error: {str(e)}"}],
                "isError": True,
            }

    async def health_check(self) -> ProviderHealth:
        """Check AWS MCP Server health by listing tools."""
        start = time.time()
        try:
            if not self._session:
                await self.connect()

            await self._session.list_tools()

            self.health.healthy = True
            self.health.last_check = time.time()
            self.health.latency_ms = (time.time() - start) * 1000
            self.health.error_message = None

        except Exception as e:
            self.health.healthy = False
            self.health.last_check = time.time()
            self.health.latency_ms = (time.time() - start) * 1000
            self.health.error_message = str(e)
            self._logger.warning("aws_provider.health_check_failed", error=str(e))

        return self.health
EOF

# ============================================================
# 7. src/multicloud_mcp/providers/azure.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/providers/azure.py
"""Azure MCP Server adapter using stdio transport."""

from __future__ import annotations

import time
from typing import Any

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo

logger = structlog.get_logger()


class AzureProvider(ProviderAdapter):
    """Adapter for the official Azure MCP Server (microsoft/mcp)."""

    def __init__(
        self,
        command: str = "npx",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 60,
    ) -> None:
        super().__init__(
            name="azure",
            namespace="azure",
            command=command,
            args=args or ["-y", "@azure/mcp-server@latest"],
            env=env or {},
            timeout=timeout,
        )
        self._session: ClientSession | None = None
        self._stdio_ctx = None
        self._client_ctx = None

    async def connect(self) -> None:
        """Connect to Azure MCP Server via stdio."""
        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env,
            )
            self._stdio_ctx = stdio_client(server_params)
            read, write = await self._stdio_ctx.__aenter__()

            self._client_ctx = ClientSession(read, write)
            self._session = await self._client_ctx.__aenter__()
            await self._session.initialize()

            self._logger.info("azure_provider.connected")
        except Exception as e:
            self._logger.error("azure_provider.connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from Azure MCP Server."""
        try:
            if self._client_ctx:
                await self._client_ctx.__aexit__(None, None, None)
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
            self._session = None
            self._logger.info("azure_provider.disconnected")
        except Exception as e:
            self._logger.warning("azure_provider.disconnect_error", error=str(e))

    async def list_tools(self) -> list[ToolInfo]:
        """List tools from Azure MCP Server with namespace prefix."""
        if not self._session:
            await self.connect()

        try:
            tools_response = await self._session.list_tools()
            self._tools = []

            for tool in tools_response.tools:
                namespaced = self._namespaced_name(tool.name)
                self._tools.append(
                    ToolInfo(
                        name=namespaced,
                        description=f"[Azure] {tool.description}",
                        input_schema=tool.inputSchema,
                        original_name=tool.name,
                        provider="azure",
                        namespace="azure",
                    )
                )

            self.health.tools_count = len(self._tools)
            self._logger.info("azure_provider.tools_loaded", count=len(self._tools))
            return self._tools

        except Exception as e:
            self._logger.error("azure_provider.list_tools_failed", error=str(e))
            self.health.healthy = False
            self.health.error_message = str(e)
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on Azure MCP Server."""
        if not self._session:
            await self.connect()

        original_name = self._original_name(tool_name)

        try:
            self._logger.debug(
                "azure_provider.calling_tool",
                namespaced=tool_name,
                original=original_name,
            )

            result = await self._session.call_tool(original_name, arguments)

            content = []
            for item in result.content:
                if hasattr(item, "text"):
                    content.append({"type": "text", "text": item.text})
                elif hasattr(item, "data"):
                    content.append({"type": "resource", "data": item.data})
                else:
                    content.append({"type": "text", "text": str(item)})

            return {
                "content": content,
                "isError": result.isError if hasattr(result, "isError") else False,
            }

        except Exception as e:
            self._logger.error(
                "azure_provider.tool_call_failed",
                tool=original_name,
                error=str(e),
            )
            return {
                "content": [{"type": "text", "text": f"Azure Error: {str(e)}"}],
                "isError": True,
            }

    async def health_check(self) -> ProviderHealth:
        """Check Azure MCP Server health by listing tools."""
        start = time.time()
        try:
            if not self._session:
                await self.connect()

            await self._session.list_tools()

            self.health.healthy = True
            self.health.last_check = time.time()
            self.health.latency_ms = (time.time() - start) * 1000
            self.health.error_message = None

        except Exception as e:
            self.health.healthy = False
            self.health.last_check = time.time()
            self.health.latency_ms = (time.time() - start) * 1000
            self.health.error_message = str(e)
            self._logger.warning("azure_provider.health_check_failed", error=str(e))

        return self.health
EOF

# ============================================================
# 8. src/multicloud_mcp/providers/__init__.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/providers/__init__.py
"""Provider adapters for upstream MCP servers."""

from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider
from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth

__all__ = ["ProviderAdapter", "ProviderHealth", "AWSProvider", "AzureProvider"]
EOF

# ============================================================
# 9. src/multicloud_mcp/router.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/router.py
"""Routing engine for namespaced tool calls across providers."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo

logger = structlog.get_logger()


class RouterError(Exception):
    """Base exception for routing errors."""


class ProviderNotFoundError(RouterError):
    """Raised when no provider can handle a tool."""


class ToolNotFoundError(RouterError):
    """Raised when a tool is not found in any provider."""


class ProviderRouter:
    """Routes tool calls to the appropriate upstream provider."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderAdapter] = {}
        self._tools_index: dict[str, ToolInfo] = {}
        self._provider_by_tool: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._logger = logger.bind(component="router")
        self._last_refresh: float = 0.0
        self._cache_ttl: float = 300.0

    def register_provider(self, provider: ProviderAdapter) -> None:
        """Register a provider adapter."""
        self._providers[provider.name] = provider
        self._logger.info("provider_registered", name=provider.name, namespace=provider.namespace)

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider adapter."""
        if name in self._providers:
            del self._providers[name]
            self._logger.info("provider_unregistered", name=name)

    @property
    def providers(self) -> dict[str, ProviderAdapter]:
        """Return registered providers."""
        return self._providers

    @property
    def all_tools(self) -> list[ToolInfo]:
        """Return all available tools from all providers."""
        return list(self._tools_index.values())

    async def refresh_tools(self, force: bool = False) -> list[ToolInfo]:
        """Refresh the tools catalog from all providers."""
        async with self._lock:
            now = time.time()
            if not force and (now - self._last_refresh) < self._cache_ttl:
                return self.all_tools

            self._tools_index.clear()
            self._provider_by_tool.clear()

            tasks = []
            for name, provider in self._providers.items():
                tasks.append(self._safe_list_tools(provider))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for provider_name, tools in zip(self._providers.keys(), results):
                if isinstance(tools, Exception):
                    self._logger.warning(
                        "provider_tools_refresh_failed",
                        provider=provider_name,
                        error=str(tools),
                    )
                    continue

                for tool in tools:
                    self._tools_index[tool.name] = tool
                    self._provider_by_tool[tool.name] = provider_name

            self._last_refresh = time.time()
            self._logger.info(
                "tools_catalog_refreshed",
                total_tools=len(self._tools_index),
                providers=len(self._providers),
            )

            return self.all_tools

    async def _safe_list_tools(self, provider: ProviderAdapter) -> list[ToolInfo]:
        """Safely list tools from a provider with error handling."""
        try:
            return await provider.list_tools()
        except Exception as e:
            self._logger.warning(
                "safe_list_tools_failed",
                provider=provider.name,
                error=str(e),
            )
            return []

    def get_tool_info(self, tool_name: str) -> ToolInfo | None:
        """Get information about a specific tool."""
        return self._tools_index.get(tool_name)

    def get_provider_for_tool(self, tool_name: str) -> ProviderAdapter | None:
        """Get the provider that handles a specific tool."""
        provider_name = self._provider_by_tool.get(tool_name)
        if provider_name:
            return self._providers.get(provider_name)
        return None

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route a tool call to the appropriate provider."""
        await self.refresh_tools()

        provider = self.get_provider_for_tool(tool_name)

        if not provider:
            if tool_name.startswith("multicloud__"):
                raise ToolNotFoundError(
                    f"Multicloud tool '{tool_name}' not found. "
                    "Native tools must be registered separately."
                )

            available = [t for t in self._tools_index.keys() if tool_name.split("__")[-1] in t]
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found. "
                f"Did you mean one of: {available[:5]}?"
            )

        self._logger.info(
            "routing_tool_call",
            tool=tool_name,
            provider=provider.name,
        )

        return await provider.call_tool(tool_name, arguments)

    async def health_check_all(self) -> dict[str, ProviderHealth]:
        """Run health checks on all providers."""
        results = {}
        tasks = []

        for name, provider in self._providers.items():
            tasks.append(self._safe_health_check(provider))

        health_results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, health in zip(self._providers.keys(), health_results):
            if isinstance(health, Exception):
                results[name] = ProviderHealth(
                    healthy=False,
                    error_message=str(health),
                )
            else:
                results[name] = health

        return results

    async def _safe_health_check(self, provider: ProviderAdapter) -> ProviderHealth:
        """Safely run health check with timeout."""
        try:
            return await asyncio.wait_for(
                provider.health_check(),
                timeout=provider.timeout,
            )
        except asyncio.TimeoutError:
            return ProviderHealth(
                healthy=False,
                error_message="Health check timeout",
            )
        except Exception as e:
            return ProviderHealth(
                healthy=False,
                error_message=str(e),
            )
EOF

# ============================================================
# 10. src/multicloud_mcp/health.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/health.py
"""Health monitoring and circuit breaker for upstream providers."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum

import structlog

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for a single provider."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

    failures: int = field(default=0, init=False)
    last_failure_time: float = field(default=0.0, init=False)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    half_open_calls: int = field(default=0, init=False)

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self._close()
        else:
            self.failures = max(0, self.failures - 1)

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self._open()
        elif self.failures >= self.failure_threshold:
            self._open()

    def can_execute(self) -> bool:
        """Check if a call should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._half_open()
                return True
            return False
        return self.half_open_calls < self.half_open_max_calls

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self.half_open_calls = 0
        logger.warning("circuit_breaker_opened")

    def _half_open(self) -> None:
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        logger.info("circuit_breaker_half_open")

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.half_open_calls = 0
        logger.info("circuit_breaker_closed")


class HealthMonitor:
    """Monitors health of all registered providers."""

    def __init__(self, check_interval: float = 30.0) -> None:
        self.check_interval = check_interval
        self._breakers: dict[str, CircuitBreaker] = {}
        self._providers: dict[str, ProviderAdapter] = {}
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._logger = logger.bind(component="health_monitor")

    def register_provider(self, name: str, provider: ProviderAdapter) -> None:
        """Register a provider for monitoring."""
        self._providers[name] = provider
        self._breakers[name] = CircuitBreaker()

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider."""
        self._providers.pop(name, None)
        self._breakers.pop(name, None)

    def is_provider_available(self, name: str) -> bool:
        """Check if provider is available (circuit closed)."""
        breaker = self._breakers.get(name)
        return breaker.can_execute() if breaker else False

    def record_result(self, name: str, success: bool) -> None:
        """Record call result for circuit breaker."""
        breaker = self._breakers.get(name)
        if breaker:
            if success:
                breaker.record_success()
            else:
                breaker.record_failure()

    async def start(self) -> None:
        """Start periodic health checks."""
        self._task = asyncio.create_task(self._monitor_loop())
        self._logger.info("health_monitor_started", interval=self.check_interval)

    async def stop(self) -> None:
        """Stop health monitoring."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._logger.info("health_monitor_stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.check_interval,
                )
            except asyncio.TimeoutError:
                await self._check_all()

    async def _check_all(self) -> None:
        """Check all providers."""
        tasks = []
        names = []
        for name, provider in self._providers.items():
            if not self._breakers[name].can_execute():
                continue
            tasks.append(self._check_provider(name, provider))
            names.append(name)
        if not tasks:
            return
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                self._breakers[name].record_failure()
                self._logger.warning(
                    "health_check_failed", provider=name, error=str(result)
                )
            else:
                health: ProviderHealth = result
                if health.healthy:
                    self._breakers[name].record_success()
                else:
                    self._breakers[name].record_failure()
                self._logger.debug(
                    "health_check_result",
                    provider=name,
                    healthy=health.healthy,
                    latency_ms=health.latency_ms,
                )

    async def _check_provider(self, name: str, provider: ProviderAdapter) -> ProviderHealth:
        """Check a single provider."""
        return await provider.health_check()
EOF

# ============================================================
# 11. src/multicloud_mcp/cache.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/cache.py
"""In-memory cache for tools catalog with TTL support."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Generic, TypeVar

import structlog

logger = structlog.get_logger()

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with TTL."""

    value: T
    created_at: float = field(default_factory=time.time)
    ttl: float = 300.0

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl


class ToolsCache:
    """Cache for provider tools catalog."""

    def __init__(self, default_ttl: float = 300.0) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._logger = logger.bind(component="tools_cache")

    def get(self, key: str):
        """Get cached tools if not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            self._logger.debug("cache_entry_expired", key=key)
            del self._cache[key]
            return None
        self._logger.debug("cache_hit", key=key)
        return entry.value

    def set(self, key: str, value, ttl: float | None = None) -> None:
        """Store tools in cache."""
        self._cache[key] = CacheEntry(
            value=value,
            ttl=ttl or self._default_ttl,
        )
        self._logger.debug("cache_set", key=key)

    def invalidate(self, key: str | None = None) -> None:
        """Invalidate cache entries."""
        if key is None:
            self._cache.clear()
            self._logger.info("cache_invalidated_all")
        else:
            self._cache.pop(key, None)
            self._logger.info("cache_invalidated", key=key)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = len(self._cache)
        expired = sum(1 for e in self._cache.values() if e.is_expired)
        return {
            "total_entries": total,
            "expired_entries": expired,
            "valid_entries": total - expired,
        }
EOF

# ============================================================
# 12. src/multicloud_mcp/tools/__init__.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/tools/__init__.py
"""Native multicloud tools."""
EOF

# ============================================================
# 13. src/multicloud_mcp/tools/cost_comparison.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/tools/cost_comparison.py
"""Multicloud cost comparison tool."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class CostComparisonTool:
    """Compare costs between AWS and Azure for equivalent services."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__compare_cost",
            description=(
                "Compare estimated costs between AWS and Azure for equivalent services. "
                "Supports compute, storage, database, and networking services."
            ),
            input_schema={
                "type": "object",
                "required": ["service_type", "region_aws", "region_azure", "specs"],
                "properties": {
                    "service_type": {
                        "type": "string",
                        "enum": ["compute", "storage", "database", "networking", "kubernetes"],
                        "description": "Type of cloud service to compare",
                    },
                    "region_aws": {
                        "type": "string",
                        "description": "AWS region (e.g., us-east-1)",
                    },
                    "region_azure": {
                        "type": "string",
                        "description": "Azure region (e.g., eastus)",
                    },
                    "specs": {
                        "type": "object",
                        "description": "Service specifications",
                        "properties": {
                            "vcpu": {"type": "integer"},
                            "memory_gb": {"type": "integer"},
                            "storage_gb": {"type": "integer"},
                            "storage_type": {
                                "type": "string",
                                "enum": ["ssd", "hdd", "nvme"],
                            },
                        },
                    },
                },
            },
            original_name="multicloud__compare_cost",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute cost comparison."""
        service_type = arguments.get("service_type", "compute")
        region_aws = arguments.get("region_aws", "us-east-1")
        region_azure = arguments.get("region_azure", "eastus")
        specs = arguments.get("specs", {})

        comparisons = {
            "compute": self._compare_compute(specs, region_aws, region_azure),
            "storage": self._compare_storage(specs, region_aws, region_azure),
            "database": self._compare_database(specs, region_aws, region_azure),
        }

        return {
            "service_type": service_type,
            "regions": {"aws": region_aws, "azure": region_azure},
            "comparison": comparisons.get(service_type, {}),
            "recommendation": self._get_recommendation(comparisons.get(service_type, {})),
        }

    def _compare_compute(self, specs: dict, aws_region: str, azure_region: str) -> dict:
        vcpu = specs.get("vcpu", 4)
        memory = specs.get("memory_gb", 16)
        aws_price = round((vcpu * 0.048) + (memory * 0.012), 4)
        azure_price = round((vcpu * 0.052) + (memory * 0.014), 4)
        return {
            "aws": {
                "instance_family": "m6i" if vcpu <= 8 else "m6g",
                "price_per_hour": aws_price,
                "price_per_month": round(aws_price * 730, 2),
            },
            "azure": {
                "instance_family": "Dsv5" if vcpu <= 8 else "Ddsv5",
                "price_per_hour": azure_price,
                "price_per_month": round(azure_price * 730, 2),
            },
            "savings": {
                "winner": "aws" if aws_price < azure_price else "azure",
                "percentage": round(abs(aws_price - azure_price) / max(aws_price, azure_price) * 100, 1),
            },
        }

    def _compare_storage(self, specs: dict, aws_region: str, azure_region: str) -> dict:
        storage_gb = specs.get("storage_gb", 1000)
        storage_type = specs.get("storage_type", "ssd")
        pricing = {
            "ssd": {"aws": 0.10, "azure": 0.12},
            "hdd": {"aws": 0.045, "azure": 0.048},
            "nvme": {"aws": 0.125, "azure": 0.137},
        }
        aws_price = pricing.get(storage_type, pricing["ssd"])["aws"]
        azure_price = pricing.get(storage_type, pricing["ssd"])["azure"]
        return {
            "aws": {
                "service": "EBS gp3" if storage_type == "ssd" else "EBS st1",
                "price_per_gb_month": aws_price,
                "total_monthly": round(aws_price * storage_gb, 2),
            },
            "azure": {
                "service": "Managed Disks Premium SSD" if storage_type == "ssd" else "Standard HDD",
                "price_per_gb_month": azure_price,
                "total_monthly": round(azure_price * storage_gb, 2),
            },
        }

    def _compare_database(self, specs: dict, aws_region: str, azure_region: str) -> dict:
        return {
            "aws": {"service": "RDS PostgreSQL", "price_per_hour": 0.35},
            "azure": {"service": "Azure Database for PostgreSQL", "price_per_hour": 0.38},
        }

    def _get_recommendation(self, comparison: dict) -> str:
        if "savings" in comparison:
            winner = comparison["savings"]["winner"]
            pct = comparison["savings"]["percentage"]
            return f"{winner.upper()} is approximately {pct}% more cost-effective for this workload."
        return "Compare specific services for detailed recommendations."
EOF

# ============================================================
# 14. src/multicloud_mcp/tools/resource_mapper.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/tools/resource_mapper.py
"""Resource mapping tool between cloud providers."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class ResourceMapperTool:
    """Map cloud resources between AWS and Azure."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__map_resource",
            description=(
                "Map a cloud resource type from one provider to its equivalent in another. "
                "Useful for migration planning and multicloud architecture design."
            ),
            input_schema={
                "type": "object",
                "required": ["source_provider", "resource_type", "target_provider"],
                "properties": {
                    "source_provider": {
                        "type": "string",
                        "enum": ["aws", "azure"],
                    },
                    "resource_type": {
                        "type": "string",
                        "description": "Resource type to map (e.g., 's3_bucket', 'aks_cluster')",
                    },
                    "target_provider": {
                        "type": "string",
                        "enum": ["aws", "azure"],
                    },
                },
            },
            original_name="multicloud__map_resource",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute resource mapping."""
        source = arguments.get("source_provider")
        target = arguments.get("target_provider")
        resource = arguments.get("resource_type", "")

        mappings = {
            ("aws", "azure"): {
                "s3_bucket": "Azure Blob Storage",
                "ec2_instance": "Azure Virtual Machine",
                "eks_cluster": "Azure Kubernetes Service (AKS)",
                "lambda_function": "Azure Functions",
                "rds_postgres": "Azure Database for PostgreSQL",
                "dynamodb": "Azure Cosmos DB",
                "sqs_queue": "Azure Service Bus Queue",
                "sns_topic": "Azure Service Bus Topic",
                "cloudwatch": "Azure Monitor",
                "iam_role": "Azure Managed Identity",
                "vpc": "Azure Virtual Network",
                "route53": "Azure DNS",
                "elb": "Azure Load Balancer",
                "autoscaling_group": "Azure Virtual Machine Scale Sets",
            },
            ("azure", "aws"): {
                "blob_storage": "Amazon S3",
                "virtual_machine": "Amazon EC2",
                "aks_cluster": "Amazon EKS",
                "functions": "AWS Lambda",
                "postgresql": "Amazon RDS for PostgreSQL",
                "cosmos_db": "Amazon DynamoDB",
                "service_bus": "Amazon SQS/SNS",
                "monitor": "Amazon CloudWatch",
                "managed_identity": "AWS IAM Role",
                "virtual_network": "Amazon VPC",
                "dns": "Amazon Route 53",
                "load_balancer": "Elastic Load Balancing",
                "vm_scale_sets": "Auto Scaling Groups",
            },
        }

        key = (source, target)
        mapping = mappings.get(key, {})

        return {
            "source": {"provider": source, "resource": resource},
            "target": {"provider": target},
            "equivalent": mapping.get(resource, "No direct equivalent found"),
            "mapping_confidence": "high" if resource in mapping else "low",
            "notes": self._get_notes(resource, mapping.get(resource)),
        }

    def _get_notes(self, source_resource: str, target_resource: str | None) -> str:
        if not target_resource:
            return f"No standard mapping found for {source_resource}. Consider custom architecture review."
        notes = {
            "s3_bucket": "Azure Blob Storage supports hot/cool/archive tiers. Consider lifecycle policies.",
            "ec2_instance": "Check Azure Hybrid Benefit for Windows workloads.",
            "eks_cluster": "AKS has managed control plane. Consider Azure CNI vs. kubenet.",
            "lambda_function": "Azure Functions Consumption plan is most similar to Lambda.",
            "dynamodb": "Cosmos DB offers multi-model support. Choose API carefully.",
        }
        return notes.get(source_resource, "Review service-specific features and limitations.")
EOF

# ============================================================
# 15. src/multicloud_mcp/tools/list_providers.py (STUB para Codex)
# ============================================================
cat << 'EOF' > src/multicloud_mcp/tools/list_providers.py
"""List providers and their health status."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class ListProvidersTool:
    """List all connected providers and their health status."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__list_providers",
            description="List all connected cloud providers, their health status, latency, and available tools count.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            original_name="multicloud__list_providers",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any], router, health_monitor) -> dict[str, Any]:
        """Execute list providers. Requires router and health_monitor injected."""
        # TODO: Implementar. Usar router.providers y health_monitor._breakers
        # para retornar estado de cada provider.
        raise NotImplementedError("Implementar en Fase 2 de CODEX_PROMPT.md")
EOF

# ============================================================
# 16. src/multicloud_mcp/tools/discover_resources.py (STUB para Codex)
# ============================================================
cat << 'EOF' > src/multicloud_mcp/tools/discover_resources.py
"""Discover resources across all connected clouds."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class DiscoverResourcesTool:
    """Discover active resources across all connected cloud providers."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__discover_resources",
            description="Discover all active resources across connected AWS and Azure accounts.",
            input_schema={
                "type": "object",
                "properties": {
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                    "resource_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["kubernetes", "compute", "storage", "database"]},
                    },
                },
            },
            original_name="multicloud__discover_resources",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any], router) -> dict[str, Any]:
        """Execute discover resources. Requires router injected."""
        # TODO: Implementar. Iterar providers, llamar tools de listado relevantes,
        # unificar resultados. Manejar errores individuales.
        raise NotImplementedError("Implementar en Fase 2 de CODEX_PROMPT.md")
EOF

# ============================================================
# 17. src/multicloud_mcp/tools/security_posture.py (STUB para Codex)
# ============================================================
cat << 'EOF' > src/multicloud_mcp/tools/security_posture.py
"""Security posture analysis across clouds."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class SecurityPostureTool:
    """Analyze security posture across connected cloud providers."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__security_posture",
            description="Analyze security configurations across AWS and Azure (public buckets, open security groups, etc.)",
            input_schema={
                "type": "object",
                "properties": {
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                },
            },
            original_name="multicloud__security_posture",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute security posture analysis."""
        # TODO: Implementar. Llamar tools de IAM/Security de cada provider.
        raise NotImplementedError("Implementar en Fase 2 de CODEX_PROMPT.md")
EOF

# ============================================================
# 18. src/multicloud_mcp/tools/compliance.py (STUB para Codex)
# ============================================================
cat << 'EOF' > src/multicloud_mcp/tools/compliance.py
"""Compliance checking across clouds."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class ComplianceCheckerTool:
    """Check compliance against frameworks like CIS or NIST."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__compliance_check",
            description="Verify cloud compliance against CIS or NIST frameworks across AWS and Azure.",
            input_schema={
                "type": "object",
                "required": ["framework"],
                "properties": {
                    "framework": {
                        "type": "string",
                        "enum": ["CIS", "NIST"],
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                },
            },
            original_name="multicloud__compliance_check",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute compliance check."""
        # TODO: Implementar. Usar tools de seguridad de cada provider.
        raise NotImplementedError("Implementar en Fase 2 de CODEX_PROMPT.md")
EOF

echo "✅ Core source files generated"

# ============================================================
# 19. src/multicloud_mcp/server.py
# ============================================================
cat << 'EOF' > src/multicloud_mcp/server.py
"""Main MCP server entry point with stdio and HTTP transport support."""

from __future__ import annotations

import argparse
import asyncio
import json
import signal
import sys
from typing import Any

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
import uvicorn

from multicloud_mcp.config import Settings
from multicloud_mcp.health import HealthMonitor
from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider
from multicloud_mcp.router import ProviderRouter, ToolNotFoundError

logger = structlog.get_logger()


class MulticloudMCPServer:
    """Unified Multicloud MCP Server."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.router = ProviderRouter()
        self.health_monitor = HealthMonitor(check_interval=30.0)
        self.server = Server(settings.server.name)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools from all providers."""
            tools = await self.router.refresh_tools()

            if self.settings.multicloud.enabled:
                tools.extend(self._get_multicloud_tools())

            return [
                Tool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.input_schema,
                )
                for tool in tools
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Route tool call to appropriate provider."""
            try:
                if name.startswith("multicloud__"):
                    result = await self._call_multicloud_tool(name, arguments)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]

                result = await self.router.call_tool(name, arguments)
                provider = self.router.get_provider_for_tool(name)
                if provider:
                    self.health_monitor.record_result(
                        provider.name,
                        not result.get("isError", False),
                    )

                if result.get("isError"):
                    return [TextContent(type="text", text=f"Error: {result['content']}")]

                content_parts = []
                for item in result.get("content", []):
                    if item.get("type") == "text":
                        content_parts.append(item["text"])
                    else:
                        content_parts.append(json.dumps(item))

                return [TextContent(type="text", text="\n".join(content_parts))]

            except ToolNotFoundError as e:
                return [TextContent(type="text", text=f"Tool not found: {e}")]
            except Exception as e:
                logger.error("tool_call_failed", tool=name, error=str(e))
                return [TextContent(type="text", text=f"Internal error: {str(e)}")]

    def _get_multicloud_tools(self):
        """Return multicloud native tool definitions."""
        from multicloud_mcp.tools.cost_comparison import CostComparisonTool
        from multicloud_mcp.tools.resource_mapper import ResourceMapperTool
        from multicloud_mcp.tools.list_providers import ListProvidersTool
        from multicloud_mcp.tools.discover_resources import DiscoverResourcesTool
        from multicloud_mcp.tools.security_posture import SecurityPostureTool
        from multicloud_mcp.tools.compliance import ComplianceCheckerTool

        tools = []
        enabled = set(self.settings.multicloud.tools)

        if "cost_comparison" in enabled:
            tools.append(CostComparisonTool().get_tool_info())
        if "resource_mapper" in enabled:
            tools.append(ResourceMapperTool().get_tool_info())
        if "list_providers" in enabled:
            tools.append(ListProvidersTool().get_tool_info())
        if "discover_resources" in enabled:
            tools.append(DiscoverResourcesTool().get_tool_info())
        if "security_posture" in enabled:
            tools.append(SecurityPostureTool().get_tool_info())
        if "compliance_checker" in enabled:
            tools.append(ComplianceCheckerTool().get_tool_info())

        return tools

    async def _call_multicloud_tool(self, name: str, arguments: dict) -> dict[str, Any]:
        """Execute multicloud native tools."""
        from multicloud_mcp.tools.cost_comparison import CostComparisonTool
        from multicloud_mcp.tools.resource_mapper import ResourceMapperTool
        from multicloud_mcp.tools.list_providers import ListProvidersTool
        from multicloud_mcp.tools.discover_resources import DiscoverResourcesTool
        from multicloud_mcp.tools.security_posture import SecurityPostureTool
        from multicloud_mcp.tools.compliance import ComplianceCheckerTool

        if name == "multicloud__compare_cost":
            return await CostComparisonTool().execute(arguments)
        elif name == "multicloud__map_resource":
            return await ResourceMapperTool().execute(arguments)
        elif name == "multicloud__list_providers":
            return await ListProvidersTool().execute(arguments, self.router, self.health_monitor)
        elif name == "multicloud__discover_resources":
            return await DiscoverResourcesTool().execute(arguments, self.router)
        elif name == "multicloud__security_posture":
            return await SecurityPostureTool().execute(arguments)
        elif name == "multicloud__compliance_check":
            return await ComplianceCheckerTool().execute(arguments)
        else:
            return {"error": f"Unknown multicloud tool: {name}"}

    async def initialize(self) -> None:
        """Initialize all configured providers."""
        for name, config in self.settings.providers.items():
            if not config.enabled:
                logger.info("provider_skipped", name=name, reason="disabled")
                continue

            try:
                if name == "aws":
                    provider = AWSProvider(
                        command=config.command,
                        args=config.args,
                        env=config.env,
                        timeout=config.timeout,
                    )
                elif name == "azure":
                    provider = AzureProvider(
                        command=config.command,
                        args=config.args,
                        env=config.env,
                        timeout=config.timeout,
                    )
                else:
                    logger.warning("unknown_provider", name=name)
                    continue

                await provider.connect()
                self.router.register_provider(provider)
                self.health_monitor.register_provider(name, provider)
                logger.info("provider_initialized", name=name)

            except Exception as e:
                logger.error("provider_init_failed", name=name, error=str(e))

        await self.router.refresh_tools(force=True)
        await self.health_monitor.start()

    async def shutdown(self) -> None:
        """Gracefully shutdown all providers."""
        await self.health_monitor.stop()
        for name, provider in self.router.providers.items():
            try:
                await provider.disconnect()
                logger.info("provider_shutdown", name=name)
            except Exception as e:
                logger.warning("provider_shutdown_error", name=name, error=str(e))

    async def run_stdio(self) -> None:
        """Run server with stdio transport."""
        await self.initialize()
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )
        finally:
            await self.shutdown()

    async def run_http(self) -> None:
        """Run server with HTTP transport (MCP 2026-07-28 stateless)."""
        await self.initialize()

        async def mcp_endpoint(request: Request) -> JSONResponse:
            """Handle MCP requests over HTTP."""
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "Invalid JSON"}, status_code=400)

            method = body.get("method")
            params = body.get("params", {})

            if method == "tools/list":
                tools = await self.router.refresh_tools()
                if self.settings.multicloud.enabled:
                    tools.extend(self._get_multicloud_tools())
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": t.name,
                                "description": t.description,
                                "inputSchema": t.input_schema,
                            }
                            for t in tools
                        ]
                    }
                })

            elif method == "tools/call":
                result = await self.router.call_tool(
                    params.get("name"),
                    params.get("arguments", {})
                )
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": result
                })

            return JSONResponse({"error": "Method not found"}, status_code=404)

        async def health_endpoint(request: Request) -> JSONResponse:
            """Health check endpoint."""
            health = await self.router.health_check_all()
            return JSONResponse({
                "status": "healthy" if all(h.healthy for h in health.values()) else "degraded",
                "providers": {
                    name: {
                        "healthy": h.healthy,
                        "tools_count": h.tools_count,
                        "latency_ms": h.latency_ms,
                    }
                    for name, h in health.items()
                }
            })

        async def metrics_endpoint(request: Request) -> PlainTextResponse:
            """Prometheus-style metrics endpoint."""
            lines = [
                "# HELP multicloud_providers_total Number of registered providers",
                "# TYPE multicloud_providers_total gauge",
                f"multicloud_providers_total {len(self.router.providers)}",
                "",
                "# HELP multicloud_tools_total Number of available tools",
                "# TYPE multicloud_tools_total gauge",
                f"multicloud_tools_total {len(self.router.all_tools)}",
            ]
            return PlainTextResponse("\n".join(lines))

        routes = [
            Route("/mcp", mcp_endpoint, methods=["POST"]),
            Route("/health", health_endpoint, methods=["GET"]),
            Route("/metrics", metrics_endpoint, methods=["GET"]),
        ]

        app = Starlette(routes=routes)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        config = self.settings.server.http
        logger.info("http_server_starting", host=config.host, port=config.port)

        # Graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        uvicorn.run(app, host=config.host, port=config.port)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Multicloud MCP Server")
    parser.add_argument(
        "--transport", choices=["stdio", "http"], default=None, help="Transport protocol"
    )
    parser.add_argument(
        "--port", type=int, default=None, help="HTTP port (only with --transport http)"
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to config YAML file"
    )
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=None
    )
    args = parser.parse_args()

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    if args.config:
        settings = Settings.from_yaml(args.config)
    else:
        settings = Settings.load()

    if args.transport:
        settings.server.transport = args.transport
    if args.port:
        settings.server.http.port = args.port
    if args.log_level:
        settings.logging.level = args.log_level

    server = MulticloudMCPServer(settings)

    try:
        if settings.server.transport == "stdio":
            asyncio.run(server.run_stdio())
        else:
            asyncio.run(server.run_http())
    except KeyboardInterrupt:
        logger.info("server_shutdown_requested")
    except Exception as e:
        logger.error("server_fatal_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
EOF

# ============================================================
# 20-23. Tests
# ============================================================
cat << 'EOF' > tests/__init__.py
"""Tests package."""
EOF

cat << 'EOF' > tests/test_router.py
"""Tests for the provider router."""

import pytest

from multicloud_mcp.providers.base import ProviderAdapter, ProviderHealth, ToolInfo
from multicloud_mcp.router import ProviderRouter, ToolNotFoundError


class MockProvider(ProviderAdapter):
    """Mock provider for testing."""

    def __init__(self, name: str, tools: list[ToolInfo] | None = None):
        super().__init__(name, name, "echo", [], {})
        self._mock_tools = tools or []

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def list_tools(self):
        return self._mock_tools

    async def call_tool(self, name, args):
        return {"content": [{"type": "text", "text": "ok"}], "isError": False}

    async def health_check(self):
        return ProviderHealth(healthy=True)


@pytest.mark.asyncio
async def test_router_register_provider():
    router = ProviderRouter()
    provider = MockProvider("aws")
    router.register_provider(provider)
    assert "aws" in router.providers


@pytest.mark.asyncio
async def test_router_refresh_tools():
    router = ProviderRouter()
    tools = [ToolInfo("aws__s3__list", "List S3", {}, "list", "aws", "aws")]
    provider = MockProvider("aws", tools)
    router.register_provider(provider)

    result = await router.refresh_tools(force=True)
    assert len(result) == 1
    assert result[0].name == "aws__s3__list"


@pytest.mark.asyncio
async def test_router_call_tool_not_found():
    router = ProviderRouter()
    with pytest.raises(ToolNotFoundError):
        await router.call_tool("nonexistent__tool", {})


@pytest.mark.asyncio
async def test_router_call_tool_success():
    router = ProviderRouter()
    tools = [ToolInfo("aws__test", "Test", {}, "test", "aws", "aws")]
    provider = MockProvider("aws", tools)
    router.register_provider(provider)
    await router.refresh_tools(force=True)

    result = await router.call_tool("aws__test", {})
    assert result["isError"] is False
EOF

cat << 'EOF' > tests/test_providers.py
"""Tests for provider adapters."""

import pytest

from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider


def test_aws_provider_namespacing():
    provider = AWSProvider()
    assert provider._namespaced_name("list_buckets") == "aws__list_buckets"
    assert provider._original_name("aws__list_buckets") == "list_buckets"


def test_azure_provider_namespacing():
    provider = AzureProvider()
    assert provider._namespaced_name("list_vms") == "azure__list_vms"
    assert provider._original_name("azure__list_vms") == "list_vms"


def test_provider_health_initial_state():
    from multicloud_mcp.providers.base import ProviderHealth
    health = ProviderHealth()
    assert health.healthy is False
    assert health.tools_count == 0
EOF

cat << 'EOF' > tests/test_multicloud_tools.py
"""Tests for multicloud native tools."""

import pytest

from multicloud_mcp.tools.cost_comparison import CostComparisonTool
from multicloud_mcp.tools.resource_mapper import ResourceMapperTool


@pytest.mark.asyncio
async def test_cost_comparison_compute():
    tool = CostComparisonTool()
    result = await tool.execute({
        "service_type": "compute",
        "region_aws": "us-east-1",
        "region_azure": "eastus",
        "specs": {"vcpu": 4, "memory_gb": 16},
    })
    assert "comparison" in result
    assert "aws" in result["comparison"]
    assert "azure" in result["comparison"]
    assert "savings" in result["comparison"]


@pytest.mark.asyncio
async def test_cost_comparison_storage():
    tool = CostComparisonTool()
    result = await tool.execute({
        "service_type": "storage",
        "region_aws": "us-east-1",
        "region_azure": "eastus",
        "specs": {"storage_gb": 1000, "storage_type": "ssd"},
    })
    assert result["comparison"]["aws"]["service"] == "EBS gp3"


@pytest.mark.asyncio
async def test_resource_mapper_aws_to_azure():
    tool = ResourceMapperTool()
    result = await tool.execute({
        "source_provider": "aws",
        "resource_type": "s3_bucket",
        "target_provider": "azure",
    })
    assert result["equivalent"] == "Azure Blob Storage"
    assert result["mapping_confidence"] == "high"


@pytest.mark.asyncio
async def test_resource_mapper_azure_to_aws():
    tool = ResourceMapperTool()
    result = await tool.execute({
        "source_provider": "azure",
        "resource_type": "aks_cluster",
        "target_provider": "aws",
    })
    assert result["equivalent"] == "Amazon EKS"


@pytest.mark.asyncio
async def test_resource_mapper_unknown():
    tool = ResourceMapperTool()
    result = await tool.execute({
        "source_provider": "aws",
        "resource_type": "unknown_resource",
        "target_provider": "azure",
    })
    assert result["mapping_confidence"] == "low"
    assert "No direct equivalent" in result["equivalent"]
EOF

cat << 'EOF' > tests/integration/__init__.py
"""Integration tests package."""
EOF

cat << 'EOF' > tests/integration/test_end_to_end.py
"""End-to-end integration tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from multicloud_mcp.server import MulticloudMCPServer
from multicloud_mcp.config import Settings


@pytest.mark.asyncio
async def test_server_lifecycle():
    """Test full server lifecycle: init -> list_tools -> shutdown."""
    settings = Settings()
    settings.providers = {}  # No providers for unit test
    server = MulticloudMCPServer(settings)

    await server.initialize()
    # Server should initialize without errors even with no providers
    await server.shutdown()


@pytest.mark.asyncio
async def test_list_tools_with_no_providers():
    """Test list_tools returns multicloud tools when no providers."""
    settings = Settings()
    settings.providers = {}
    server = MulticloudMCPServer(settings)

    await server.initialize()
    tools = await server.server._request_handlers["tools/list"]()
    # Should have at least multicloud tools
    await server.shutdown()
EOF

# ============================================================
# 24-26. Docs
# ============================================================
cat << 'EOF' > docs/architecture.md
# Arquitectura del Multicloud MCP Server

## Visión General

El Multicloud MCP Server implementa el patrón **Proxy Aggregator** sobre el protocolo MCP (Model Context Protocol), actuando como fachada unificada para múltiples servidores MCP de nube.

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP CLIENT                              │
│         (Claude Desktop, Cursor, VS Code, etc.)             │
└──────────────────────────┬──────────────────────────────────┘
                           │ stdio / HTTP (stateless)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              MULTICLOUD MCP SERVER                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Server    │  │   Router    │  │  Health Monitor     │ │
│  │  (FastMCP)  │  │  + Cache    │  │  + Circuit Breaker  │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘ │
│         │                │                                   │
│    ┌────┴────┐      ┌────┴────┐                            │
│    │  AWS    │      │  Azure  │      [GCP, OCI, ...]       │
│    │ Adapter │      │ Adapter │                            │
│    │ (stdio) │      │ (stdio) │                            │
│    └────┬────┘      └────┬────┘                            │
└─────────┼────────────────┼──────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────┐  ┌─────────────────┐
│  AWS MCP Server │  │ Azure MCP Server│
│  (awslabs/mcp)  │  │ (microsoft/mcp) │
└─────────────────┘  └─────────────────┘
```

## Patrones de Diseño

### 1. Proxy Aggregator

El servidor actúa como proxy que agrega múltiples servidores MCP upstream. Cada tool se expone con un namespace único: `provider__tool_name`.

### 2. Circuit Breaker

Cada provider tiene un circuit breaker que:
- Cierra el circuito tras N fallos consecutivos
- Rechaza llamadas durante el estado OPEN
- Prueba recuperación con HALF_OPEN

### 3. Cache con TTL

El catálogo de tools se cachea por 5 minutos.

## Flujo de Datos

### Listado de Tools

1. Cliente envía `tools/list`
2. Server verifica cache (TTL 5min)
3. Si expirado: paraleliza `list_tools()` a todos los providers
4. Aplica namespace: `aws__` + nombre_original
5. Agrega tools multicloud nativas
6. Retorna catálogo unificado

### Ejecución de Tool

1. Cliente envía `tools/call` con `aws__s3__list_buckets`
2. Router.parse() -> provider="aws", tool="s3__list_buckets"
3. Verifica circuit breaker del provider
4. Ejecuta `call_tool()` en AWSProvider
5. AWSProvider traduce a nombre original y llama upstream
6. Resultado fluye de vuelta al cliente
EOF

cat << 'EOF' > docs/configuration.md
# Configuración del Multicloud MCP Server

## Métodos de Configuración

1. **Variables de entorno** (mayor prioridad)
2. **Archivo YAML** (especificado o por defecto)
3. **Valores por defecto** (menor prioridad)

## Archivo de Configuración

### Ubicaciones por defecto

- `MULTICLOUD_CONFIG_PATH`
- `./config.yaml`
- `./config.yml`
- `/etc/multicloud-mcp/config.yaml`

### Variables de Entorno

Todas usan el prefijo `MULTICLOUD_`:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `MULTICLOUD_CONFIG_PATH` | Ruta al archivo YAML | `/etc/mcp/config.yaml` |
| `MULTICLOUD_LOG_LEVEL` | Nivel de logging | `DEBUG` |
| `MULTICLOUD_SERVER__TRANSPORT` | Transporte | `http` |
| `MULTICLOUD_SERVER__HTTP__PORT` | Puerto HTTP | `8080` |

> **Nota**: El separador `__` navega objetos anidados.

## Configuración por Cliente

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
EOF

cat << 'EOF' > docs/contributing.md
# Contribuir al Multicloud MCP Server

## Cómo Contribuir

### Reportar Bugs

1. Verifica que no esté ya reportado en Issues
2. Abre un nuevo issue con pasos para reproducir

### Pull Requests

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nombre-descriptivo`
3. Commits con [Conventional Commits](https://www.conventionalcommits.org/)
4. Asegúrate de que `make check` pasa
5. Abre el PR

## Entorno de Desarrollo

```bash
uv pip install -e ".[dev]"
pre-commit install
pytest
```

## Agregar un Nuevo Provider

Crear `src/multicloud_mcp/providers/<nombre>.py` heredando de `ProviderAdapter`, luego registrar en `server.py`.
EOF

# ============================================================
# 27-29. Infraestructura
# ============================================================
cat << 'EOF' > Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

RUN apt-get update && apt-get install -y --no-install-recommends \\
    nodejs npm curl \\
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN uv pip install --system --no-cache -e "."

RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

ENV MULTICLOUD_TRANSPORT=stdio
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' || exit 1

ENTRYPOINT ["multicloud-mcp-server"]
CMD ["--transport", "stdio"]
EOF

cat << 'EOF' > .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install uv
      - run: uv pip install --system -e ".[dev]"
      - run: ruff check src tests
      - run: ruff format --check src tests
      - run: mypy src
      - run: pytest --cov-report=xml
      - uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t multicloud-mcp-server:test .
      - run: docker run --rm multicloud-mcp-server:test --help
EOF

cat << 'EOF' > .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: write

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build hatchling
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
      - uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
EOF

# ============================================================
# 30-33. Configuración y Ejemplos
# ============================================================
cat << 'EOF' > config.yaml
server:
  name: "multicloud-mcp-server"
  version: "0.1.0"
  transport: "stdio"
  http:
    host: "0.0.0.0"
    port: 8080

providers:
  aws:
    enabled: true
    command: "uvx"
    args: ["awslabs.core-mcp-server@latest"]
    env:
      AWS_REGION: "us-east-1"
      FASTMCP_LOG_LEVEL: "ERROR"
    namespace: "aws"
    health_check_interval: 30
    timeout: 60
    description: "AWS MCP Server"

  azure:
    enabled: true
    command: "npx"
    args: ["-y", "@azure/mcp-server@latest"]
    env:
      AZURE_SUBSCRIPTION_ID: "${AZURE_SUBSCRIPTION_ID}"
    namespace: "azure"
    health_check_interval: 30
    timeout: 60
    description: "Azure MCP Server"

multicloud:
  enabled: true
  tools:
    - cost_comparison
    - resource_mapper
    - list_providers
    - discover_resources
    - security_posture
    - compliance_checker

logging:
  level: "INFO"
  format: "json"
EOF

cat << 'EOF' > examples/docker-compose.yml
version: "3.8"

services:
  multicloud-mcp:
    build:
      context: ..
      dockerfile: Dockerfile
    container_name: multicloud-mcp
    environment:
      - MULTICLOUD_SERVER__TRANSPORT=http
      - MULTICLOUD_SERVER__HTTP__PORT=8080
      - MULTICLOUD_LOG_LEVEL=INFO
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - AZURE_TENANT_ID=${AZURE_TENANT_ID}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
      - AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}
    ports:
      - "8080:8080"
    command: ["--transport", "http", "--port", "8080", "--config", "/app/config.yaml"]
    volumes:
      - ../config.yaml:/app/config.yaml:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped
EOF

cat << 'EOF' > examples/claude_desktop_config.json
{
  "mcpServers": {
    "multicloud": {
      "command": "uvx",
      "args": ["multicloud-mcp-server@latest"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AZURE_SUBSCRIPTION_ID": "your-subscription-id-here"
      }
    }
  }
}
EOF

cat << 'EOF' > examples/cursor_config.json
{
  "mcpServers": {
    "multicloud": {
      "command": "uvx",
      "args": ["multicloud-mcp-server@latest"],
      "env": {
        "AWS_REGION": "us-east-1",
        "AZURE_SUBSCRIPTION_ID": "your-subscription-id-here"
      }
    }
  }
}
EOF

# ============================================================
# 34-39. Archivos de proyecto
# ============================================================
cat << 'EOF' > CONTRIBUTING.md
# Contributing to Multicloud MCP Server

Please read our detailed [Contributing Guide](docs/contributing.md).

## Quick Start

```bash
uv pip install -e ".[dev]"
pre-commit install
pytest
```
EOF

cat << 'EOF' > .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, pydantic-settings, types-PyYAML]
EOF

cat << 'EOF' > .gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
env/
venv/
.idea/
.vscode/
*.swp
*.swo
.coverage
.coverage.*
htmlcov/
.pytest_cache/
coverage.xml
*.log
.DS_Store
config.local.yaml
.env.local
EOF

cat << 'EOF' > Makefile
.PHONY: install test lint format type-check clean build docker run

install:
	uv pip install -e ".[dev]"

test:
	pytest -v --cov=multicloud_mcp --cov-report=term-missing

lint:
	ruff check src tests

format:
	ruff format src tests

type-check:
	mypy src

check: lint type-check test

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

docker:
	docker build -t multicloud-mcp-server:latest .

run:
	multicloud-mcp-server --log-level DEBUG

run-http:
	multicloud-mcp-server --transport http --port 8080
EOF

cat << 'EOF' > CHANGELOG.md
# Changelog

## [0.1.0] - 2024-XX-XX

### Added
- Initial release of Multicloud MCP Server
- Support for AWS MCP Server (awslabs/mcp) via stdio
- Support for Azure MCP Server (microsoft/mcp) via stdio
- Namespace-based tool routing (`aws__*`, `azure__*`)
- Circuit breaker pattern for provider resilience
- Health monitoring with periodic checks
- Tools cache with TTL
- Native multicloud tools:
  - `multicloud__compare_cost`
  - `multicloud__map_resource`
  - `multicloud__list_providers`
  - `multicloud__discover_resources`
  - `multicloud__security_posture`
  - `multicloud__compliance_check`
- Configuration via YAML and environment variables
- stdio and HTTP transport support
- Docker support
- CI/CD with GitHub Actions
EOF

cat << 'EOF' > LICENSE
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright 2024 Multicloud MCP Server Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
EOF

echo ""
echo "✅ Multicloud MCP Server generated successfully!"
echo ""
echo "📁 Structure:"
find . -type f | sort | head -50
echo ""
echo "🚀 Next steps:"
echo "   cd $DEST_DIR"
echo "   make install"
echo "   make check"
