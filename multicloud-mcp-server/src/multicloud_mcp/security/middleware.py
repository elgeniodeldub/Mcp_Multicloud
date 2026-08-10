"""HTTP security middleware."""

from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from multicloud_mcp.security.auth import (
    AuthenticationError,
    AuthorizationError,
    BearerAuthenticator,
)
from multicloud_mcp.security.rate_limit import InMemoryRateLimiter, RateLimitExceededError


class RequestTooLargeError(Exception):
    """Raised when an HTTP request exceeds its configured body limit."""


class SecurityMiddleware:
    """ASGI middleware for request IDs, auth, body limits, rate limits, and headers."""

    def __init__(
        self,
        app: ASGIApp,
        authenticator: BearerAuthenticator,
        protect_metrics: bool,
        max_request_size: int,
        rate_limiter: InMemoryRateLimiter | None,
        metrics: dict[str, int],
    ) -> None:
        self.app = app
        self.authenticator = authenticator
        self.protect_metrics = protect_metrics
        self.max_request_size = max_request_size
        self.rate_limiter = rate_limiter
        self.metrics = metrics

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
        client_ip = (scope.get("client") or ("unknown", 0))[0]
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id
        scope["state"]["client_ip"] = client_ip

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.extend(
                    [
                        (b"x-request-id", request_id.encode()),
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"cache-control", b"no-store"),
                    ]
                )
                message = {**message, "headers": response_headers}
            await send(message)

        path = scope.get("path", "")
        self.metrics["requests"] += 1
        try:
            if path == "/mcp" or (path == "/metrics" and self.protect_metrics):
                self.authenticator.validate_request(Request(scope, receive=receive))
            if path == "/mcp" and self.rate_limiter is not None:
                self.rate_limiter.check(client_ip)
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
            await self._error(send_with_headers, 401, "unauthorized", request_id)
        except AuthorizationError:
            self.metrics["auth_failures"] += 1
            await self._error(send_with_headers, 403, "forbidden", request_id)
        except RateLimitExceededError:
            self.metrics["rate_limit_rejections"] += 1
            await self._error(
                send_with_headers, 429, "rate_limit_exceeded", request_id, retry_after="60"
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
        retry_after: str | None = None,
    ) -> None:
        body = json.dumps({"error": error, "request_id": request_id}).encode()
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ]
        if retry_after:
            headers.append((b"retry-after", retry_after.encode()))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})
