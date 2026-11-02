"""HTTP security middleware."""

from __future__ import annotations

import inspect
import ipaddress
import json
import uuid
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from multicloud_mcp.security.auth import (
    AuthenticationError,
    Authenticator,
    AuthorizationError,
)
from multicloud_mcp.security.rate_limit import RateLimiter, RateLimitExceededError

IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network


class RequestTooLargeError(Exception):
    """Raised when an HTTP request exceeds its configured body limit."""


def parse_networks(values: Iterable[str]) -> tuple[IPNetwork, ...]:
    """Parse trusted proxy addresses/CIDRs, rejecting invalid entries at startup."""
    return tuple(ipaddress.ip_network(value.strip(), strict=False) for value in values)


def resolve_client_ip(peer: str, forwarded_for: str | None, trusted: tuple[IPNetwork, ...]) -> str:
    """Return the real client IP, honouring X-Forwarded-For only from trusted proxies.

    The header is walked right to left and the first hop that is not itself a
    trusted proxy wins, so a client cannot spoof its address by prepending values.
    """
    if not trusted or not forwarded_for or not _in_networks(peer, trusted):
        return peer
    for hop in reversed([item.strip() for item in forwarded_for.split(",") if item.strip()]):
        try:
            ipaddress.ip_address(hop)
        except ValueError:
            return peer
        if not _in_networks(hop, trusted):
            return hop
    return peer


def _in_networks(value: str, networks: tuple[IPNetwork, ...]) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(address in network for network in networks)


class SecurityMiddleware:
    """ASGI middleware for request IDs, auth, body limits, rate limits, and headers."""

    def __init__(
        self,
        app: ASGIApp,
        authenticator: Authenticator,
        protect_metrics: bool,
        max_request_size: int,
        rate_limiter: RateLimiter | None,
        metrics: dict[str, int],
        trusted_proxies: tuple[IPNetwork, ...] = (),
        strict_transport_security: bool = False,
    ) -> None:
        self.app = app
        self.authenticator = authenticator
        self.protect_metrics = protect_metrics
        self.max_request_size = max_request_size
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.trusted_proxies = trusted_proxies
        self.strict_transport_security = strict_transport_security

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        incoming_id = headers.get(b"x-request-id", b"").decode("latin-1")
        request_id = (
            incoming_id
            if 0 < len(incoming_id) <= 128
            and all(char.isalnum() or char in "._:-" for char in incoming_id)
            else str(uuid.uuid4())
        )
        peer = (scope.get("client") or ("unknown", 0))[0]
        forwarded = headers.get(b"x-forwarded-for")
        client_ip = resolve_client_ip(
            peer, forwarded.decode("latin-1") if forwarded else None, self.trusted_proxies
        )
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id
        scope["state"]["client_ip"] = client_ip
        scope["state"]["principal"] = None

        security_headers = [
            (b"x-request-id", request_id.encode()),
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
            (b"cache-control", b"no-store"),
            (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
        ]
        if self.strict_transport_security:
            security_headers.append(
                (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
            )

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.extend(security_headers)
                message = {**message, "headers": response_headers}
            await send(message)

        path = scope.get("path", "")
        self.metrics["requests"] += 1
        try:
            if path == "/mcp" or (path == "/metrics" and self.protect_metrics):
                principal = self.authenticator.validate_request(Request(scope, receive=receive))
                scope["state"]["principal"] = principal
            if path == "/mcp" and self.rate_limiter is not None:
                principal = scope["state"]["principal"]
                # Authenticated callers are limited per identity, anonymous ones per IP.
                key = f"sub:{principal.subject}" if principal else f"ip:{client_ip}"
                outcome: Any = self.rate_limiter.check(key)
                if inspect.isawaitable(outcome):
                    await outcome
            content_length = int(headers.get(b"content-length", b"0") or 0)
            if path == "/mcp" and content_length > self.max_request_size:
                self.metrics["request_size_rejections"] += 1
                await self._error(send_with_headers, 413, "request_too_large", request_id)
                return

            received = 0

            async def limited_receive() -> Message:
                nonlocal received
                message = await receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if path == "/mcp" and received > self.max_request_size:
                        raise RequestTooLargeError
                return message

            await self.app(scope, limited_receive, send_with_headers)
        except AuthenticationError:
            self.metrics["auth_failures"] += 1
            await self._error(
                send_with_headers,
                401,
                "unauthorized",
                request_id,
                extra_headers=[(b"www-authenticate", b'Bearer realm="multicloud-mcp"')],
            )
        except AuthorizationError:
            self.metrics["auth_failures"] += 1
            await self._error(send_with_headers, 403, "forbidden", request_id)
        except RateLimitExceededError:
            self.metrics["rate_limit_rejections"] += 1
            await self._error(
                send_with_headers,
                429,
                "rate_limit_exceeded",
                request_id,
                extra_headers=[(b"retry-after", b"60")],
            )
        except RequestTooLargeError:
            self.metrics["request_size_rejections"] += 1
            await self._error(send_with_headers, 413, "request_too_large", request_id)

    @staticmethod
    async def _error(
        send: Callable[[Message], Awaitable[None]],
        status: int,
        error: str,
        request_id: str,
        extra_headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        body = json.dumps({"error": error, "request_id": request_id}).encode()
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
            *(extra_headers or []),
        ]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
