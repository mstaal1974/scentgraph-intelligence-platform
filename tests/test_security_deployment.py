from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from aromatwin.config import DEFAULT_DEVELOPMENT_ORIGINS, Settings
from aromatwin.main import create_app
from aromatwin.security import REDACTED, redact_sensitive_fields, validate_cors_origins


def production_settings(**changes: object) -> Settings:
    values: dict[str, object] = {
        "environment": "production",
        "admin_api_key": "admin-secret",
        "private_api_key": "private-secret",
        "allowed_origins": ("https://store.example",),
    }
    values.update(changes)
    return Settings(**values)


def test_development_app_starts_with_safe_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.is_local
    assert settings.allowed_origins == DEFAULT_DEVELOPMENT_ORIGINS
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize("missing", ["admin_api_key", "private_api_key"])
def test_production_requires_internal_secrets(missing: str) -> None:
    with pytest.raises(ValidationError, match="Production requires configured secrets"):
        production_settings(**{missing: None})


def test_admin_endpoint_requires_correct_key_in_production() -> None:
    with TestClient(create_app(production_settings())) as client:
        assert client.get("/admin/health").status_code == 401
        assert client.get("/admin/health", headers={"X-Admin-API-Key": "wrong"}).status_code == 401
        assert client.get(
            "/admin/health", headers={"X-Admin-API-Key": "admin-secret"}
        ).status_code == 200


def test_private_supplier_endpoint_requires_correct_key_in_production() -> None:
    with TestClient(create_app(production_settings())) as client:
        assert client.get("/supplier-items").status_code == 401
        response = client.get(
            "/supplier-items", headers={"X-Private-API-Key": "private-secret"}
        )
        assert response.status_code == 200


def test_maison_public_responses_remain_private_field_free(assert_public_safe) -> None:
    with TestClient(create_app(production_settings())) as client:
        response = client.get("/maison/fragrances")
        assert response.status_code == 200
        assert_public_safe(response.json())


def test_recursive_redaction_handles_sensitive_variants() -> None:
    value = {
        "supplier_price": "10",
        "nested": [{"QTY": 3, "name": "safe"}],
        "product_cost": 4,
    }
    assert redact_sensitive_fields(value) == {
        "supplier_price": REDACTED,
        "nested": [{"QTY": REDACTED, "name": "safe"}],
        "product_cost": REDACTED,
    }


def test_cors_origins_are_parsed_deduplicated_and_normalised() -> None:
    settings = Settings(
        _env_file=None,
        allowed_origins="https://one.example/, https://two.example,https://one.example/",
    )
    assert validate_cors_origins(settings) == ["https://one.example", "https://two.example"]


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="Wildcard CORS"):
        production_settings(allowed_origins=("*",))


def test_security_headers_openapi_and_health() -> None:
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get("/health", headers={"X-Request-ID": "test-request"})
        assert response.status_code == 200
        assert response.headers["x-request-id"] == "test-request"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert client.get("/openapi.json").status_code == 200


def test_dockerignore_excludes_private_supplier_material() -> None:
    content = Path(".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "data/private" in content
    assert "private" in content
    assert "*supplier*.xlsx" in content
