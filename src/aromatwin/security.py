"""Small, dependency-free security primitives for HTTP boundaries."""

from collections.abc import Mapping
from secrets import compare_digest
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from aromatwin.config import Settings, get_settings

SENSITIVE_FIELDS = frozenset(
    {
        "price", "cost", "supplier_price", "aed", "usd", "cn_code", "supplier_code",
        "stock", "quantity", "qty", "commercial_terms", "supplier_terms",
    }
)
REDACTED = "[REDACTED]"


def _normalise_key(value: object) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def _key_matches_sensitive(key: object) -> bool:
    normalised = _normalise_key(key)
    return normalised in SENSITIVE_FIELDS or any(
        normalised.endswith(f"_{field}") for field in SENSITIVE_FIELDS
    )


def redact_sensitive_fields(value: Any) -> Any:
    """Recursively copy a structure while replacing values under sensitive keys."""
    if isinstance(value, Mapping):
        return {
            key: REDACTED if _key_matches_sensitive(key) else redact_sensitive_fields(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_fields(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_fields(item) for item in value)
    return value


def validate_cors_origins(settings: Settings) -> list[str]:
    origins = [origin.rstrip("/") for origin in settings.allowed_origins if origin]
    if settings.environment == "production" and "*" in origins:
        raise ValueError("Wildcard CORS origins are not permitted in production")
    return list(dict.fromkeys(origins))


def _require_key(provided: str | None, expected: str | None, settings: Settings) -> None:
    if settings.is_local:
        return
    if not expected or not provided or not compare_digest(provided, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "A valid API key is required")


def require_admin_api_key(
    x_admin_api_key: str | None = Header(default=None, alias="X-Admin-API-Key"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    _require_key(x_admin_api_key or x_api_key, settings.admin_api_key, settings)


def require_private_api_key(
    x_private_api_key: str | None = Header(default=None, alias="X-Private-API-Key"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    _require_key(x_private_api_key or x_api_key, settings.private_api_key, settings)


def optional_public_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """Accept an optional public key, rejecting only an incorrect configured key."""
    if x_api_key and settings.api_key and not compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid public API key")
    return x_api_key
