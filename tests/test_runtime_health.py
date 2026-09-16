from aromatwin.services.runtime_health import runtime_health, runtime_readiness


def test_public_health_is_minimal_and_secret_free() -> None:
    payload = runtime_health().model_dump()
    assert set(payload) == {"status", "service", "version"}


def test_private_readiness_masks_path_and_secrets() -> None:
    payload = runtime_readiness({"AROMATWIN_PRIVATE_API_KEY": "secret-value", "DATABASE_URL": "postgresql://u:p@host/db", "PRIVATE_STORAGE_ROOT": "/var/lib/aromatwin/private"}).model_dump_json()
    assert "secret-value" not in payload
    assert "u:p" not in payload
    assert "/var/lib/aromatwin" not in payload
    assert "[PATH:private]" in payload
