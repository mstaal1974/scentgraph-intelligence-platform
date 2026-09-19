"""Small, dependency-free security primitives for HTTP boundaries."""

import logging
from collections.abc import Mapping
from secrets import compare_digest
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from aromatwin.config import Settings, get_settings

LOGGER = logging.getLogger("aromatwin.security")

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


def _unauthorised() -> HTTPException:
    """Return one indistinguishable rejection for every authentication failure mode."""
    return HTTPException(status.HTTP_401_UNAUTHORIZED, "A valid API key is required")


def _require_key(
    provided: str | None, expected: str | None, settings: Settings, surface: str
) -> None:
    """Authenticate a request, denying by default.

    A surface with no configured credential cannot authenticate anyone, so it denies unless a
    local environment has explicitly opted in via AROMATWIN_ALLOW_INSECURE_LOCAL_AUTH. Settings
    validation already refuses to start a non-local environment with missing keys, so the
    unconfigured path is only reachable during local development.
    """
    if not expected:
        if settings.is_local and settings.allow_insecure_local_auth:
            return
        LOGGER.warning(
            "Denying %s request: no API key is configured for this surface in environment %r",
            surface,
            settings.environment,
        )
        raise _unauthorised()
    if not provided or not compare_digest(provided, expected):
        raise _unauthorised()


def require_admin_api_key(
    x_admin_api_key: str | None = Header(default=None, alias="X-Admin-API-Key"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    _require_key(x_admin_api_key or x_api_key, settings.admin_api_key, settings, "admin")


def require_private_api_key(
    x_private_api_key: str | None = Header(default=None, alias="X-Private-API-Key"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    _require_key(x_private_api_key or x_api_key, settings.private_api_key, settings, "private")


def require_public_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str | None:
    """Require a valid public key on the licensed retailer surface.

    This is the boundary every metered plan is attributed against, so an anonymous caller is
    rejected rather than served. The returned key is the caller identity later quota and usage
    accounting will hang off.
    """
    _require_key(x_api_key, settings.api_key, settings, "public")
    return x_api_key
