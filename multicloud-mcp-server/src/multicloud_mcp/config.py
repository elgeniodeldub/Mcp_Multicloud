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
