"""Redaction helpers for audit logs."""

from __future__ import annotations

from typing import Any

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "access_key",
    "secret_key",
    "client_secret",
}


def redact(value: Any) -> Any:
    """Recursively redact common secret-bearing mapping keys."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value
