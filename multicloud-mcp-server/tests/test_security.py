"""HTTP security tests."""

import httpx
import pytest

from multicloud_mcp.config import Settings
from multicloud_mcp.security.auth import (
    AuthorizationError,
    BearerAuthenticator,
)
from multicloud_mcp.security.policy import ToolBlockedError, ToolSecurityPolicy
from multicloud_mcp.security.redaction import redact
from multicloud_mcp.server import MulticloudMCPServer


async def request(app, method: str, path: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


def settings(**security_overrides) -> Settings:
    data = {"server": {"transport": "http"}, "security": security_overrides}
    return Settings.model_validate(data)


@pytest.mark.asyncio
async def test_auth_disabled_allows_mcp_and_health_is_public() -> None:
    app = MulticloudMCPServer(settings()).create_http_app()
    mcp = await request(
        app, "POST", "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    health = await request(app, "GET", "/health")
    assert mcp.status_code == 200
    assert health.status_code == 200
    assert mcp.headers["x-content-type-options"] == "nosniff"
    assert mcp.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_auth_missing_wrong_and_valid_token(monkeypatch) -> None:
    monkeypatch.setenv("MULTICLOUD_API_KEY", "super-secret-token")
    security = {"authentication": {"enabled": True}, "rate_limit": {"enabled": False}}
    app = MulticloudMCPServer(settings(**security)).create_http_app()
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    assert (await request(app, "POST", "/mcp", json=payload)).status_code == 401
    assert (
        await request(app, "POST", "/mcp", json=payload, headers={"Authorization": "Basic wrong"})
    ).status_code == 401
    assert (
        await request(app, "POST", "/mcp", json=payload, headers={"Authorization": "Bearer wrong"})
    ).status_code == 403
    valid = await request(
        app, "POST", "/mcp", json=payload, headers={"Authorization": "Bearer super-secret-token"}
    )
    assert valid.status_code == 200
    assert (await request(app, "GET", "/health")).status_code == 200
    assert (await request(app, "GET", "/metrics")).status_code == 401


def test_authenticator_does_not_use_plain_equality() -> None:
    authenticator = BearerAuthenticator(True, "TEST_KEY", expected_token="secret")
    request_scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": [(b"authorization", b"Bearer bad")],
    }
    with pytest.raises(AuthorizationError):
        from starlette.requests import Request

        authenticator.validate_request(Request(request_scope, receive=lambda: None))  # type: ignore[arg-type]
    assert authenticator.enabled


def test_security_config_rejects_wildcard_with_auth() -> None:
    with pytest.raises(ValueError, match="allowed_origins"):
        Settings.model_validate(
            {"security": {"authentication": {"enabled": True}, "cors": {"allowed_origins": ["*"]}}}
        )


@pytest.mark.asyncio
async def test_cors_is_explicit_and_request_size_is_limited(monkeypatch) -> None:
    monkeypatch.setenv("MULTICLOUD_API_KEY", "secret")
    security = {
        "authentication": {"enabled": True},
        "cors": {"enabled": True, "allowed_origins": ["http://allowed.example"]},
        "max_request_size_bytes": 100,
        "rate_limit": {"enabled": False},
    }
    app = MulticloudMCPServer(settings(**security)).create_http_app()
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "padding": "x" * 200}
    response = await request(
        app,
        "POST",
        "/mcp",
        json=payload,
        headers={"Authorization": "Bearer secret", "Origin": "http://allowed.example"},
    )
    assert response.status_code == 413
    assert response.headers.get("access-control-allow-origin") == "http://allowed.example"


@pytest.mark.asyncio
async def test_rate_limit_returns_retry_after(monkeypatch) -> None:
    monkeypatch.setenv("MULTICLOUD_API_KEY", "secret")
    app = MulticloudMCPServer(
        settings(
            authentication={"enabled": True}, rate_limit={"enabled": True, "requests_per_minute": 1}
        )
    ).create_http_app()
    headers = {"Authorization": "Bearer secret"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    assert (await request(app, "POST", "/mcp", json=payload, headers=headers)).status_code == 200
    limited = await request(app, "POST", "/mcp", json=payload, headers=headers)
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"


def test_read_only_policy_blocks_provider_mutations_but_allows_native_tools() -> None:
    policy = ToolSecurityPolicy("read_only")
    policy.authorize_tool("aws__ec2__describe_instances")
    policy.authorize_tool("finops__get_actual_costs")
    with pytest.raises(ToolBlockedError):
        policy.authorize_tool("aws__ec2__terminate_instances")
    with pytest.raises(ToolBlockedError):
        policy.authorize_tool("azure__vm__restart")


def test_redaction_hides_secret_keys() -> None:
    result = redact({"token": "secret", "nested": {"client_secret": "hidden", "name": "ok"}})
    assert result == {
        "token": "[REDACTED]",
        "nested": {"client_secret": "[REDACTED]", "name": "ok"},
    }
