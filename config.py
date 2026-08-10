"""Configuration management using Pydantic Settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        """Load settings from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from file or environment."""
        config_path = os.environ.get("MULTICLOUD_CONFIG_PATH")

        if config_path and Path(config_path).exists():
            return cls.from_yaml(config_path)

        # Try default locations
        for default_path in ["config.yaml", "config.yml", "/etc/multicloud-mcp/config.yaml"]:
            if Path(default_path).exists():
                return cls.from_yaml(default_path)

        return cls()


def get_default_config() -> dict[str, Any]:
    """Generate a default configuration dictionary."""
    return {
        "server": {
            "name": "multicloud-mcp-server",
            "version": "0.1.0",
            "transport": "stdio",
        },
        "providers": {
            "aws": {
                "enabled": True,
                "command": "uvx",
                "args": ["awslabs.core-mcp-server@latest"],
                "env": {
                    "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
                    "FASTMCP_LOG_LEVEL": "ERROR",
                },
                "namespace": "aws",
                "health_check_interval": 30,
                "description": "AWS MCP Server — comprehensive AWS API access",
            },
            "azure": {
                "enabled": True,
                "command": "npx",
                "args": ["-y", "@azure/mcp-server@latest"],
                "env": {
                    "AZURE_SUBSCRIPTION_ID": os.environ.get("AZURE_SUBSCRIPTION_ID", ""),
                },
                "namespace": "azure",
                "health_check_interval": 30,
                "description": "Azure MCP Server — Azure resource management",
            },
        },
        "multicloud": {
            "enabled": True,
            "tools": [
                "cost_comparison",
                "resource_mapper",
                "security_posture",
                "compliance_checker",
            ],
        },
        "logging": {
            "level": "INFO",
            "format": "json",
        },
    }
