"""Validate staging configuration without disclosing configuration values."""

import os
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from aromatwin.schemas.deployment import EnvironmentReadinessReport, EnvironmentVariableCheck

BLOCKING = frozenset({
    "blocked_missing_secret", "blocked_missing_database", "blocked_invalid_storage_path",
    "blocked_unsafe_cors", "blocked_invalid_environment",
})
BOOLEAN_NAMES = (
    "ENABLE_PUBLIC_API", "ENABLE_PRIVATE_WORKFLOWS", "ENABLE_PERSISTENCE",
    "ENABLE_REVIEW_WORKFLOW", "ENABLE_PRIVATE_PILOT", "ENABLE_PLATFORM_COMPLETION",
)


def _get(env: Mapping[str, str], name: str) -> str | None:
    return env.get(name) or env.get(f"AROMATWIN_{name}")


def _enabled(env: Mapping[str, str], name: str, default: bool = False) -> bool:
    value = _get(env, name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def mask_value(name: str, value: str | None) -> str:
    """Return only a non-reversible description suitable for logs and reports."""
    if not value:
        return "[NOT SET]"
    if name in {"AROMATWIN_API_KEY", "AROMATWIN_PRIVATE_API_KEY", "DATABASE_URL"}:
        return "[SET]"
    if "STORAGE" in name or "ROOT" in name:
        return f"[PATH:{Path(value).name or '/'}]"
    return "[SET]"


def check_environment_readiness(
    environ: Mapping[str, str] | None = None,
    *,
    allowed_private_roots: tuple[Path, ...] | None = None,
) -> EnvironmentReadinessReport:
    env = os.environ if environ is None else environ
    environment = (_get(env, "ENV") or _get(env, "ENVIRONMENT") or "not_configured").lower()
    allowed = allowed_private_roots or (Path("data/private").resolve(), Path("/var/lib/aromatwin"))
    checks: list[EnvironmentVariableCheck] = []
    blockers: list[str] = []
    warnings: list[str] = []

    def add(name: str, status: str, message: str, required: bool = False) -> None:
        value = _get(env, name.removeprefix("AROMATWIN_")) or env.get(name)
        checks.append(EnvironmentVariableCheck(name=name, status=status, masked_value=mask_value(name, value),
                                               required=required, message=message))
        (blockers if status in BLOCKING else warnings if status == "warning" else []).append(message)

    if environment not in {"staging", "development", "dev", "local", "test", "testing", "production"}:
        add("AROMATWIN_ENV", "blocked_invalid_environment", "Set AROMATWIN_ENV to an explicit supported mode.", True)
    else:
        add("AROMATWIN_ENV", "ready", f"Environment mode is {environment}.", True)
    private_key = _get(env, "PRIVATE_API_KEY")
    add("AROMATWIN_PRIVATE_API_KEY", "ready" if private_key else "blocked_missing_secret",
        "Private API key is configured." if private_key else "Configure the private API key in the host secret store.", True)
    add("AROMATWIN_API_KEY", "ready" if _get(env, "API_KEY") else "not_configured",
        "Public API key status recorded; its value is never exposed.")
    persistence = _enabled(env, "ENABLE_PERSISTENCE")
    database = _get(env, "DATABASE_URL")
    add("DATABASE_URL", "ready" if database else ("blocked_missing_database" if persistence else "not_configured"),
        "Database connection is configured." if database else "Configure a database before enabling persistence.", persistence)
    storage = _get(env, "PRIVATE_STORAGE_ROOT")
    storage_ok = False
    if storage:
        resolved = Path(storage).expanduser().resolve()
        storage_ok = any(resolved == root.resolve() or root.resolve() in resolved.parents for root in allowed)
    storage_status = "ready" if storage_ok else ("blocked_invalid_storage_path" if storage else "not_configured")
    add("PRIVATE_STORAGE_ROOT", storage_status,
        "Private storage is within an allowed root." if storage_ok else "Configure private storage beneath an allowed private root.", True)
    add("PUBLIC_SAMPLE_ROOT", "ready" if _get(env, "PUBLIC_SAMPLE_ROOT") else "not_configured",
        "Public sample root status recorded.")
    cors = _get(env, "CORS_ALLOWED_ORIGINS") or _get(env, "ALLOWED_ORIGINS")
    if cors and "*" in {part.strip() for part in cors.split(",")}:
        cors_status = "blocked_unsafe_cors" if environment in {"staging", "production"} else "warning"
        add("CORS_ALLOWED_ORIGINS", cors_status, "Wildcard CORS is not safe for hosted staging.", True)
    else:
        add("CORS_ALLOWED_ORIGINS", "ready" if cors else "not_configured",
            "CORS origins are explicit." if cors else "Configure explicit staging CORS origins.", True)
    if _enabled(env, "ENABLE_PUBLIC_API") and environment != "staging":
        add("ENABLE_PUBLIC_API", "warning", "Public API is enabled without explicit staging mode.")
    else:
        add("ENABLE_PUBLIC_API", "ready", "Public API mode is consistent with the environment.")
    for name in BOOLEAN_NAMES[1:]:
        add(name, "ready" if _get(env, name) is not None else "not_configured", "Feature flag status recorded.")
    add("LOG_LEVEL", "ready" if _get(env, "LOG_LEVEL") else "not_configured", "Log level status recorded.")
    overall = checks[0].status
    for check in checks:
        if check.status in BLOCKING:
            overall = check.status
            break
    else:
        overall = "warning" if warnings else "ready"
    return EnvironmentReadinessReport(environment=environment, overall_status=overall, checks=checks,
                                      blocking_issues=blockers, warnings=warnings,
                                      created_at=datetime.now(UTC))
