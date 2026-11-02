"""Smoke-test the Azure MCP server version pinned in config.yaml.

Starts the configured command over stdio, performs the MCP handshake, and lists
tools. No Azure credentials are needed: listing tools does not call Azure.
Pass --version to test a different @azure/mcp release (for example, to check
whether a newer version fixed a platform-specific crash).
"""

from __future__ import annotations

import argparse
import asyncio
import re
import shutil
import sys
from pathlib import Path

import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def azure_command(config_path: Path, version: str | None) -> tuple[str, list[str]]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    azure = config["providers"]["azure"]
    args = [str(arg) for arg in azure.get("args", [])]
    if version:
        args = [re.sub(r"^@azure/mcp@.+$", f"@azure/mcp@{version}", arg) for arg in args]
    command = shutil.which(str(azure["command"])) or str(azure["command"])
    return command, args


async def run(command: str, args: list[str], timeout: float) -> int:
    params = StdioServerParameters(command=command, args=args)
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await asyncio.wait_for(session.initialize(), timeout)
        tools = await asyncio.wait_for(session.list_tools(), timeout)
    print(f"azure-mcp ok: {len(tools.tools)} tools via {' '.join([command, *args])}")
    return 0 if tools.tools else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--version", help="Override the pinned @azure/mcp version")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    command, command_args = azure_command(args.config, args.version)
    try:
        return asyncio.run(run(command, command_args, args.timeout))
    except Exception as exc:
        print(f"azure-mcp smoke test failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
