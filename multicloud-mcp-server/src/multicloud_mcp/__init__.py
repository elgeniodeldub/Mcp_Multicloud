"""Multicloud MCP Server: unified MCP gateway for AWS, Azure, and GCP FinOps."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("multicloud-mcp-server")
except PackageNotFoundError:  # pragma: no cover - running from a source tree
    __version__ = "0.0.0+unknown"
__all__ = ["create_server", "main"]
