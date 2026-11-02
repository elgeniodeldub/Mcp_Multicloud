"""Runtime tests for the HTTP server."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

import multicloud_mcp.server as server_module
from multicloud_mcp.config import Settings
from multicloud_mcp.server import MulticloudMCPServer


@pytest.mark.asyncio
async def test_run_http_works_when_signal_handlers_are_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Windows event loops may not implement add_signal_handler."""
    settings = Settings()
    settings.server.transport = "http"
    server = MulticloudMCPServer(settings)
    served = False

    async def fake_initialize() -> None:
        return None

    def unsupported_signal_handler(*args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    class FakeUvicornServer:
        def __init__(self, config: Any) -> None:
            self.config = config

        async def serve(self) -> None:
            nonlocal served
            served = True

    monkeypatch.setattr(server, "initialize", fake_initialize)
    monkeypatch.setattr(server, "create_http_app", lambda: object())
    monkeypatch.setattr(
        asyncio.get_running_loop(), "add_signal_handler", unsupported_signal_handler
    )
    monkeypatch.setattr(server_module.uvicorn, "Server", FakeUvicornServer)

    await server.run_http()

    assert served is True
