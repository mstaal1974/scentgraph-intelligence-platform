from pathlib import Path

from aromatwin.services.environment_readiness import check_environment_readiness


def base_env(tmp_path: Path) -> dict[str, str]:
    private = tmp_path / "private"
    return {
        "AROMATWIN_ENV": "staging", "AROMATWIN_PRIVATE_API_KEY": "do-not-disclose",
        "DATABASE_URL": "postgresql://user:password@example.invalid/db",
        "PRIVATE_STORAGE_ROOT": str(private), "CORS_ALLOWED_ORIGINS": "https://stage.example.invalid",
        "ENABLE_PERSISTENCE": "true",
    }


def test_environment_masks_secrets(tmp_path: Path) -> None:
    env = base_env(tmp_path)
    report = check_environment_readiness(env, allowed_private_roots=(tmp_path,))
    payload = report.model_dump_json()
    assert "do-not-disclose" not in payload
    assert "user:password" not in payload
    assert all(check.masked_value in {"[SET]", "[NOT SET]", "[PATH:private]"} for check in report.checks)


def test_missing_private_key_blocks(tmp_path: Path) -> None:
    env = base_env(tmp_path)
    env.pop("AROMATWIN_PRIVATE_API_KEY")
    assert check_environment_readiness(env, allowed_private_roots=(tmp_path,)).overall_status == "blocked_missing_secret"


def test_missing_database_blocks_when_persistence_enabled(tmp_path: Path) -> None:
    env = base_env(tmp_path)
    env.pop("DATABASE_URL")
    report = check_environment_readiness(env, allowed_private_roots=(tmp_path,))
    assert any(check.status == "blocked_missing_database" for check in report.checks)


def test_unsafe_cors_and_storage_escape_are_blocked(tmp_path: Path) -> None:
    env = base_env(tmp_path)
    env["CORS_ALLOWED_ORIGINS"] = "*"
    env["PRIVATE_STORAGE_ROOT"] = "/tmp/public"
    report = check_environment_readiness(env, allowed_private_roots=(tmp_path,))
    statuses = {check.status for check in report.checks}
    assert "blocked_unsafe_cors" in statuses
    assert "blocked_invalid_storage_path" in statuses
