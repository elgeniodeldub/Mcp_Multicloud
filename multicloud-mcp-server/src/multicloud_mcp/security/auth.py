"""Bearer API-key authentication for HTTP transport."""

from __future__ import annotations

import os
import secrets

from starlette.requests import Request


class AuthenticationError(Exception):
    """Raised when credentials are missing or malformed."""


class AuthorizationError(Exception):
    """Raised when supplied credentials are invalid."""


class BearerAuthenticator:
    """Validate a bearer token loaded only from the configured environment variable."""

    def __init__(self, enabled: bool, api_key_env: str, expected_token: str | None = None) -> None:
        self.enabled = enabled
        self.api_key_env = api_key_env
        self._expected_token = (
            expected_token if expected_token is not None else os.environ.get(api_key_env)
        )
        if enabled and not self._expected_token:
            raise ValueError(
                f"HTTP authentication is enabled but environment variable '{api_key_env}' is not set"
            )

    def validate_request(self, request: Request) -> None:
        """Validate the Authorization header without ever logging either token."""
        if not self.enabled:
            return

        header = request.headers.get("authorization")
        if not header or not header.startswith("Bearer "):
            raise AuthenticationError("Authorization header must use Bearer authentication")

        token = header[7:].strip()
        if not token:
            raise AuthenticationError("Bearer token is required")
        if not secrets.compare_digest(token, self._expected_token or ""):
            raise AuthorizationError("Invalid bearer token")
