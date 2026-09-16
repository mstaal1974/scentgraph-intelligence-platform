"""Aggregate repository and environment evidence for a human staging operator."""

import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aromatwin.schemas.deployment import DeploymentReadinessReport
from aromatwin.services.environment_readiness import check_environment_readiness

TEMPLATES = (
    "deployment/staging.env.example", "deployment/render.yaml.example",
    "deployment/railway.json.example", "deployment/fly.toml.example",
    "deployment/docker-compose.staging.example.yml",
)


def check_deployment_readiness(
    environ: Mapping[str, str] | None = None, *, root: Path = Path(".")
) -> DeploymentReadinessReport:
    env = os.environ if environ is None else environ
    environment = check_environment_readiness(env)
    blockers = list(environment.blocking_issues)
    warnings = list(environment.warnings)
    database_configured = bool(env.get("DATABASE_URL") or env.get("AROMATWIN_DATABASE_URL"))
    persistence = (env.get("ENABLE_PERSISTENCE") or env.get("AROMATWIN_ENABLE_PERSISTENCE") or "").lower() in {"1", "true", "yes", "on"}
    database_status = "ready" if database_configured else ("blocked" if persistence else "not_configured")
    migration_files = list((root / "database/migrations/versions").glob("*.py"))
    migration_status = "ready" if migration_files else "blocked"
    if not migration_files:
        blockers.append("No migration version files were found.")
    storage_check = next(check for check in environment.checks if check.name == "PRIVATE_STORAGE_ROOT")
    templates_missing = [name for name in TEMPLATES if not (root / name).is_file()]
    dependency_ready = (root / "pyproject.toml").is_file()
    docker_ready = (root / "Dockerfile").is_file()
    audit_ready = (root / "scripts/audit_deployment_privacy.py").is_file()
    if templates_missing:
        blockers.append("Deployment templates are incomplete.")
    if not dependency_ready or not docker_ready:
        blockers.append("Runtime dependency or Docker build file is missing.")
    if not audit_ready:
        blockers.append("Deployment privacy audit is missing.")
    health_ready = (root / "src/aromatwin/routers/deployment.py").is_file()
    private_routes = (root / "src/aromatwin/routers/private_pilot.py").is_file()
    samples = list((root / "data/samples").glob("*readiness_sample.csv"))
    unsafe_sample = re.compile(
        r"(?i)\b(supplier_(?:price|cost|code)|cn_code|aed_price|usd_price|raw_margin|"
        r"stock|quantity|seller_private|consumer_private|email|phone|street_address)\b"
    )
    sample_risks = [path.name for path in samples if unsafe_sample.search(path.read_text(encoding="utf-8"))]
    sample_status = "blocked" if sample_risks else ("ready" if len(samples) >= 2 else "warning")
    if sample_risks:
        blockers.append("Public readiness samples contain private or commercial field markers.")
    elif sample_status == "warning":
        warnings.append("Public-safe readiness samples are incomplete.")

    if sample_status == "blocked":
        overall = "blocked_privacy_risk"
    elif storage_check.status == "blocked_invalid_storage_path":
        overall = "blocked_storage_risk"
    elif migration_status == "blocked":
        overall = "blocked_migration_risk"
    elif blockers:
        if database_status == "blocked" and all("database" in item.lower() for item in blockers):
            overall = "ready_after_database_configured"
        elif any("key" in item.lower() or "secret" in item.lower() for item in blockers):
            overall = "ready_after_secrets_configured"
        else:
            overall = "blocked_missing_required_configuration"
    elif environment.environment != "staging":
        overall = "ready_for_staging_configuration"
    else:
        overall = "ready_for_staging_deploy"
    actions = []
    if not env.get("AROMATWIN_PRIVATE_API_KEY"):
        actions.append("Configure a private API key in the staging host secret store.")
    if not database_configured:
        actions.append("Provision and configure the staging database outside this repository.")
    if storage_check.status != "ready":
        actions.append("Mount an allowed private runtime storage path.")
    next_step = actions[0] if actions else "Run the privacy audit, then perform a human deployment review."
    return DeploymentReadinessReport(
        deployment_readiness_id=f"deploy-{uuid4()}", environment=environment.environment,
        overall_status=overall, environment_status=environment.overall_status,
        database_status=database_status, migration_status=migration_status,
        private_storage_status=storage_check.status, public_sample_status=sample_status,
        api_health_status="ready" if health_ready else "blocked",
        private_workflow_status="ready" if private_routes else "blocked",
        audit_status="ready" if audit_ready else "blocked",
        deployment_template_status="ready" if not templates_missing else "blocked",
        blocking_issues=blockers, warnings=warnings, required_operator_actions=actions,
        recommended_next_step=next_step, created_at=datetime.now(UTC),
    )
