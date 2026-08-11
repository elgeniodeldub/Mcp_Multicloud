"""Configuration management using Pydantic Settings."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def resolve_env_vars(obj: Any) -> Any:
    """Recursively resolve ${VAR} and ${VAR:-default} patterns in config."""
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    if isinstance(obj, str):
        pattern = re.compile(r"\$\{(\w+)(?::-([^}]*))?\}")

        def replacer(match: re.Match[str]) -> str:
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
    max_concurrency: int = Field(default=10, ge=1)
    retry_attempts: int = Field(default=2, ge=0, le=5)
    circuit_failure_threshold: int = Field(default=5, ge=1)
    circuit_recovery_timeout: float = Field(default=30.0, ge=1)
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
    tools: list[str] = Field(
        default_factory=lambda: [
            "actual_costs",
            "gcp_list_prices",
            "get_cost",
            "breakdown",
            "compare",
            "resource_mapper",
            "list_providers",
            "discover_resources",
            "security_posture",
            "compliance_checker",
        ]
    )


class ToolExposureConfig(BaseModel):
    """Controls which tool classes are visible to external MCP clients."""

    native_tools: bool = True
    provider_passthrough: bool = True
    provider_allowlist: list[str] = Field(default_factory=list)
    tool_allowlist: list[str] = Field(default_factory=list)
    tool_denylist: list[str] = Field(default_factory=list)


class HttpConfig(BaseModel):
    """HTTP transport configuration."""

    host: str = "127.0.0.1"
    port: int = 8080


class AuthenticationConfig(BaseModel):
    """HTTP bearer authentication settings."""

    enabled: bool = False
    type: str = "bearer"
    api_key_env: str = "MULTICLOUD_API_KEY"
    protect_metrics: bool = True

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value != "bearer":
            raise ValueError("security.authentication.type must currently be 'bearer'")
        return value

    @field_validator("api_key_env")
    @classmethod
    def validate_api_key_env(cls, value: str) -> str:
        return value


class CorsConfig(BaseModel):
    """Explicit CORS settings."""

    enabled: bool = False
    allowed_origins: list[str] = Field(default_factory=list)
    allowed_methods: list[str] = Field(default_factory=lambda: ["GET", "POST"])
    allowed_headers: list[str] = Field(default_factory=lambda: ["Authorization", "Content-Type"])

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            parsed = urlparse(origin)
            if origin == "*" or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("security.cors.allowed_origins must contain valid http(s) origins")
        return origins


class RateLimitConfig(BaseModel):
    """Single-instance HTTP rate limiting settings."""

    enabled: bool = True
    requests_per_minute: int = Field(default=60, ge=1)


class ToolPolicyConfig(BaseModel):
    """Tool safety mode."""

    mode: str = "allow_all"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in {"allow_all", "read_only"}:
            raise ValueError("security.tool_policy.mode must be 'allow_all' or 'read_only'")
        return value


class SecurityConfig(BaseModel):
    """HTTP security configuration."""

    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    max_request_size_bytes: int = Field(default=1_048_576, ge=1)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    tool_policy: ToolPolicyConfig = Field(default_factory=ToolPolicyConfig)

    @model_validator(mode="after")
    def validate_security(self) -> SecurityConfig:
        if self.authentication.enabled and not self.authentication.api_key_env.strip():
            raise ValueError(
                "security.authentication.api_key_env cannot be empty when authentication is enabled"
            )
        if self.authentication.enabled and "*" in self.cors.allowed_origins:
            raise ValueError(
                "security.cors.allowed_origins cannot contain '*' when authentication is enabled"
            )
        return self


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
    tool_exposure: ToolExposureConfig = Field(default_factory=ToolExposureConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Settings:
        """Load settings from a YAML file with env var resolution."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        resolved_data = resolve_env_vars(raw_data)
        return cls.model_validate(resolved_data)

    @classmethod
    def load(cls) -> Settings:
        """Load settings from file or environment."""
        config_path = os.environ.get("MULTICLOUD_CONFIG_PATH")

        if config_path and Path(config_path).exists():
            return cls.from_yaml(config_path)

        for default_path in ["config.yaml", "config.yml", "/etc/multicloud-mcp/config.yaml"]:
            if Path(default_path).exists():
                return cls.from_yaml(default_path)

        return cls()
