"""Public health and authenticated runtime-readiness summaries."""

import os
from collections.abc import Mapping
from pathlib import Path

from aromatwin.schemas.deployment import RuntimeHealthRead, RuntimeReadinessRead
from aromatwin.services.environment_readiness import _enabled, _get, mask_value


def runtime_health() -> RuntimeHealthRead:
    return RuntimeHealthRead(version="0.2.0")


def runtime_readiness(environ: Mapping[str, str] | None = None) -> RuntimeReadinessRead:
    env = os.environ if environ is None else environ
    storage = _get(env, "PRIVATE_STORAGE_ROOT")
    return RuntimeReadinessRead(
        app_alive=True, version_available=True,
        environment_mode=(_get(env, "ENV") or _get(env, "ENVIRONMENT") or "not_configured"),
        database_configured=bool(_get(env, "DATABASE_URL")),
        persistence_enabled=_enabled(env, "ENABLE_PERSISTENCE"),
        private_storage_configured=bool(storage),
        private_storage_path=mask_value("PRIVATE_STORAGE_ROOT", storage) if storage else None,
        review_workflow_available=_enabled(env, "ENABLE_REVIEW_WORKFLOW"),
        private_pilot_available=_enabled(env, "ENABLE_PRIVATE_PILOT"),
        platform_completion_available=_enabled(env, "ENABLE_PLATFORM_COMPLETION"),
        audit_scripts_available=Path("scripts/run_all_safe_audits.py").is_file(),
    )
