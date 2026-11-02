"""Tests for read-only policy, proxies, OIDC, scopes, Redis backends, and metrics."""

import time
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from multicloud_mcp.application.context import ExecutionContext
from multicloud_mcp.application.executor import ApplicationToolExecutor
from multicloud_mcp.cache import RedisJSONCache
from multicloud_mcp.config import Settings
from multicloud_mcp.finops.models import FinOpsCostResult, FinOpsQuery
from multicloud_mcp.finops.services.cost_service import FinOpsCostService
from multicloud_mcp.observability import ToolMetrics
from multicloud_mcp.providers.base import ToolInfo
from multicloud_mcp.router import ProviderRouter
from multicloud_mcp.security.auth import AuthorizationError, OIDCAuthenticator
from multicloud_mcp.security.middleware import parse_networks, resolve_client_ip
from multicloud_mcp.security.policy import ToolBlockedError, ToolSecurityPolicy
from multicloud_mcp.security.rate_limit import RateLimitExceededError, RedisRateLimiter
from multicloud_mcp.server import MulticloudMCPServer
from multicloud_mcp.tools.registry import NativeToolRegistry, RegisteredNativeTool


def test_read_only_requires_hint_or_allowlist_and_checks_arguments() -> None:
    policy = ToolSecurityPolicy("read_only")
    with pytest.raises(ToolBlockedError):
        policy.authorize_tool("azure__storage")
    policy.authorize_tool("azure__storage", {"command": "storage_account_list"}, True)
    with pytest.raises(ToolBlockedError, match="argument 'command'"):
        policy.authorize_tool("azure__storage", {"command": "storage_account_create"}, True)
    with pytest.raises(ToolBlockedError):
        policy.authorize_tool("azure__group", {"nested": {"intent": "delete group"}}, True)
    with pytest.raises(ToolBlockedError):
        policy.authorize_tool("aws__s3__put_object", read_only_hint=True)
    # Whole-word matching: tag/set inside longer words is not a mutation.
    policy.authorize_tool("aws__list_tags", read_only_hint=True)
    policy.authorize_tool("azure__get_settings", read_only_hint=True)
    strict = ToolSecurityPolicy("read_only", trust_read_only_hints=False)
    with pytest.raises(ToolBlockedError):
        strict.authorize_tool("azure__monitor", read_only_hint=True)


def test_forwarded_for_is_trusted_only_from_configured_proxies() -> None:
    trusted = parse_networks(["10.0.0.0/8"])
    assert resolve_client_ip("10.0.0.5", "203.0.113.7", trusted) == "203.0.113.7"
    assert resolve_client_ip("10.0.0.5", "1.1.1.1, 203.0.113.7, 10.0.0.9", trusted) == (
        "203.0.113.7"
    )
    assert resolve_client_ip("198.51.100.1", "203.0.113.7", trusted) == "198.51.100.1"
    assert resolve_client_ip("10.0.0.5", "not-an-ip", trusted) == "10.0.0.5"
    assert resolve_client_ip("10.0.0.5", "203.0.113.7", ()) == "10.0.0.5"
    with pytest.raises(ValueError):
        Settings.model_validate({"security": {"trusted_proxies": ["bogus"]}})


def test_http_refuses_remote_bind_without_auth() -> None:
    def server(host: str, **security: Any) -> MulticloudMCPServer:
        return MulticloudMCPServer(
            Settings.model_validate(
                {"server": {"transport": "http", "http": {"host": host}}, "security": security}
            )
        )

    server("127.0.0.1").validate_http_exposure()
    server("::1").validate_http_exposure()
    with pytest.raises(ValueError, match="without authentication"):
        server("0.0.0.0").validate_http_exposure()
    server("0.0.0.0", allow_unauthenticated_remote=True).validate_http_exposure()


KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ISSUER = "https://idp.example.test/"


class FakeJWKS:
    class Key:
        key = KEY.public_key()

    def get_signing_key_from_jwt(self, token: str) -> Any:
        return self.Key()


def token(**overrides: Any) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": "multicloud",
        "sub": "user-1",
        "iat": now,
        "exp": now + 300,
        "scope": "finops:read mcp",
        **overrides,
    }
    return jwt.encode(claims, KEY, algorithm="RS256")


class FakeRequest:
    def __init__(self, value: str) -> None:
        self.headers = {"authorization": f"Bearer {value}"}


def test_oidc_validates_signature_claims_and_scopes() -> None:
    auth = OIDCAuthenticator(ISSUER, "multicloud", required_scopes=["mcp"], jwks_client=FakeJWKS())
    principal = auth.validate_request(FakeRequest(token()))  # type: ignore[arg-type]
    assert principal.subject == "user-1"
    assert principal.scopes == frozenset({"finops:read", "mcp"})
    for bad in (
        token(aud="other"),
        token(iss="https://evil.test/"),
        token(exp=int(time.time()) - 600),
        token(scope="finops:read"),
        jwt.encode({"sub": "x"}, "s" * 32, algorithm="HS256"),
    ):
        with pytest.raises(AuthorizationError):
            auth.validate_request(FakeRequest(bad))  # type: ignore[arg-type]


def test_oidc_config_requires_issuer_audience_and_https() -> None:
    with pytest.raises(ValueError):
        Settings.model_validate({"security": {"authentication": {"enabled": True, "type": "oidc"}}})
    with pytest.raises(ValueError):
        Settings.model_validate(
            {"security": {"authentication": {"oidc": {"issuer": "http://idp.test"}}}}
        )


@pytest.mark.asyncio
async def test_executor_enforces_tool_scopes_for_token_callers() -> None:
    registry = NativeToolRegistry()

    async def run(arguments: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True}

    registry.register(
        RegisteredNativeTool(ToolInfo("finops__x", "", {}, "finops__x", "finops", "finops"), run)
    )
    metrics = ToolMetrics()
    executor = ApplicationToolExecutor(
        registry,
        ProviderRouter(),
        ToolSecurityPolicy(),
        tool_scopes={"finops__*": "finops:read", "*": "provider:call"},
        metrics=metrics,
    )
    allowed = ExecutionContext("r1", scopes=frozenset({"finops:read"}))
    denied = ExecutionContext("r2", scopes=frozenset({"other"}))
    api_key = ExecutionContext("r3")
    assert not (await executor.execute("finops__x", {}, allowed)).errors
    assert (await executor.execute("finops__x", {}, denied)).errors[0].code == "insufficient_scope"
    assert not (await executor.execute("finops__x", {}, api_key)).errors
    rendered = "\n".join(metrics.render())
    assert 'multicloud_tool_executions_total{tool="finops__x",outcome="success"} 2' in rendered
    assert 'outcome="insufficient_scope"} 1' in rendered
    assert 'multicloud_tool_duration_ms_count{tool="finops__x"} 3' in rendered


class FakePipeline:
    def __init__(self, store: dict[str, int], fail: bool) -> None:
        self.store = store
        self.fail = fail
        self.key = ""

    def incr(self, key: str) -> None:
        self.key = key

    def expire(self, key: str, seconds: int) -> None:
        return None

    async def execute(self) -> list[Any]:
        if self.fail:
            raise ConnectionError
        self.store[self.key] = self.store.get(self.key, 0) + 1
        return [self.store[self.key], True]


class FakeRedis:
    def __init__(self, fail: bool = False) -> None:
        self.store: dict[str, Any] = {}
        self.fail = fail

    def pipeline(self, transaction: bool) -> FakePipeline:
        return FakePipeline(self.store, self.fail)

    async def get(self, key: str) -> Any:
        if self.fail:
            raise ConnectionError
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        if self.fail:
            raise ConnectionError
        self.store[key] = value


@pytest.mark.asyncio
async def test_redis_rate_limiter_shares_counts_and_falls_back() -> None:
    redis = FakeRedis()
    first, second = RedisRateLimiter(redis, 2), RedisRateLimiter(redis, 2)
    await first.check("ip:a")
    await second.check("ip:a")
    with pytest.raises(RateLimitExceededError):
        await first.check("ip:a")
    broken = RedisRateLimiter(FakeRedis(fail=True), 1)
    await broken.check("ip:b")
    with pytest.raises(RateLimitExceededError):
        await broken.check("ip:b")


class CountingProvider:
    name = "aws"

    def __init__(self) -> None:
        self.calls = 0

    async def query_cost(self, query: FinOpsQuery) -> list[FinOpsCostResult]:
        self.calls += 1
        return [
            FinOpsCostResult(
                provider_name="aws",
                effective_cost=Decimal("1.25"),
                currency="USD",
                start_date=query.start_date,
                end_date=query.end_date,
            )
        ]


@pytest.mark.asyncio
async def test_shared_cache_is_used_across_service_instances() -> None:
    redis = FakeRedis()
    query = FinOpsQuery(start_date=date(2026, 10, 1), end_date=date(2026, 11, 1))
    provider_a, provider_b = CountingProvider(), CountingProvider()
    service_a = FinOpsCostService({"aws": provider_a}, shared_cache=RedisJSONCache(redis))
    service_b = FinOpsCostService({"aws": provider_b}, shared_cache=RedisJSONCache(redis))
    await service_a.query(query)
    response = await service_b.query(query)
    assert response.cache_hit is True
    assert response.results[0].effective_cost == Decimal("1.25")
    assert (provider_a.calls, provider_b.calls) == (1, 0)
    broken = FinOpsCostService(
        {"aws": CountingProvider()}, shared_cache=RedisJSONCache(FakeRedis(fail=True))
    )
    assert (await broken.query(query)).cache_hit is False


@pytest.mark.asyncio
async def test_http_sends_hardening_headers() -> None:
    app = MulticloudMCPServer(
        Settings.model_validate({"server": {"transport": "http"}, "security": {"hsts": True}})
    ).create_http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
    assert response.headers["strict-transport-security"].startswith("max-age=")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_shipped_configs_load(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "sub")
    container = Settings.from_yaml("docker/config.container.yaml")
    assert container.providers["azure"].command == "azmcp"
    assert container.security.authentication.enabled is True
    assert container.security.tool_policy.mode == "read_only"
    default = Settings.from_yaml("config.yaml")
    assert "forecast" in default.multicloud.tools
    Settings.from_yaml("examples/config.secure.yaml")
