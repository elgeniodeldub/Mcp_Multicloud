"""HTTP authentication: static bearer API key or OAuth 2.1 / OIDC JWT access tokens."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
import jwt
from starlette.requests import Request


class AuthenticationError(Exception):
    """Raised when credentials are missing or malformed."""


class AuthorizationError(Exception):
    """Raised when supplied credentials are invalid."""


class InsufficientScopeError(Exception):
    """Raised when a valid caller lacks the scope a tool requires."""


@dataclass(frozen=True)
class Principal:
    """Authenticated caller. ``scopes`` is None for the static API key (full access)."""

    subject: str
    scopes: frozenset[str] | None = None
    claims: dict[str, Any] = field(default_factory=dict)


class Authenticator(Protocol):
    enabled: bool

    def validate_request(self, request: Request) -> Principal | None: ...


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization")
    if not header or not header.startswith("Bearer "):
        raise AuthenticationError("Authorization header must use Bearer authentication")
    token = header[7:].strip()
    if not token:
        raise AuthenticationError("Bearer token is required")
    return token


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

    def validate_request(self, request: Request) -> Principal | None:
        """Validate the Authorization header without ever logging either token."""
        if not self.enabled:
            return None
        token = _bearer_token(request)
        if not secrets.compare_digest(token, self._expected_token or ""):
            raise AuthorizationError("Invalid bearer token")
        return Principal(subject="api-key")


class OIDCAuthenticator:
    """Validate JWT access tokens against an OIDC issuer's JWKS.

    Checks signature (asymmetric algorithms only), issuer, audience, expiry, and
    the globally required scopes. Per-tool scopes are enforced by the executor.
    """

    ALLOWED_ALGORITHMS = ("RS256", "RS384", "RS512", "ES256", "ES384", "PS256")

    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_url: str | None = None,
        required_scopes: list[str] | None = None,
        scope_claim: str = "scope",
        leeway_seconds: int = 30,
        jwks_client: Any | None = None,
    ) -> None:
        self.enabled = True
        # Compared verbatim with the token's iss claim, trailing slash included.
        self.issuer = issuer
        self.audience = audience
        self.required_scopes = frozenset(required_scopes or [])
        self.scope_claim = scope_claim
        self.leeway = leeway_seconds
        self._jwks = jwks_client or jwt.PyJWKClient(
            jwks_url or self._discover_jwks_url(issuer), cache_keys=True, lifespan=3600
        )

    @staticmethod
    def _discover_jwks_url(issuer: str) -> str:
        """Resolve jwks_uri from the issuer's OpenID Connect discovery document."""
        url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        jwks_uri = response.json().get("jwks_uri")
        if not isinstance(jwks_uri, str) or not jwks_uri.startswith("https://"):
            raise ValueError("OIDC discovery document has no https jwks_uri")
        return jwks_uri

    def validate_request(self, request: Request) -> Principal:
        token = _bearer_token(request)
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.ALLOWED_ALGORITHMS),
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthorizationError("Invalid access token") from exc
        scopes = self._scopes(claims)
        if not self.required_scopes <= scopes:
            raise AuthorizationError("Access token is missing required scopes")
        return Principal(subject=str(claims["sub"]), scopes=scopes, claims=claims)

    def _scopes(self, claims: dict[str, Any]) -> frozenset[str]:
        raw = claims.get(self.scope_claim, claims.get("scp", ""))
        if isinstance(raw, str):
            return frozenset(raw.split())
        if isinstance(raw, list):
            return frozenset(str(item) for item in raw)
        return frozenset()
