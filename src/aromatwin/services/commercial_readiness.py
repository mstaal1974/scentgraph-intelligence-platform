"""Repository evidence assessment for model review, never paid-launch approval."""

from datetime import UTC, datetime
from pathlib import Path

from aromatwin.schemas.commercial_packaging import CommercialReadinessReport
from aromatwin.services.api_entitlements import build_api_entitlement_matrix
from aromatwin.services.commercial_plans import get_commercial_plans
from aromatwin.services.tenant_feature_access import build_tenant_feature_access_matrix


def check_commercial_readiness(root: Path = Path("."), privacy_passed: bool = True) -> CommercialReadinessReport:
    plans = bool(get_commercial_plans())
    entitlements = bool(build_api_entitlement_matrix().entitlements)
    tenant_rules = bool(build_tenant_feature_access_matrix())
    api_docs = (root / "docs/api-contract.md").is_file()
    privacy_audit = (root / "scripts/audit_commercial_packaging_privacy.py").is_file()
    staging = (root / "docs/staging-deployment-readiness.md").is_file()
    maison = (root / "docs/maison-integration-readiness.md").is_file()
    scentprint = (root / "docs/scentprint-quiz-contract.md").is_file()
    privacy_ok = privacy_passed and privacy_audit
    issues = []
    status = "ready_for_commercial_model_review"
    if not entitlements:
        issues.append("Entitlement matrix is missing.")
        status = "blocked_missing_entitlements"
    elif not privacy_ok:
        issues.append("Public-file privacy audit did not pass.")
        status = "blocked_privacy_risk"
    elif not api_docs:
        issues.append("API boundary documentation is missing.")
        status = "blocked_api_boundary_unclear"
    return CommercialReadinessReport(
        readiness_id="commercial_readiness_repository", overall_status=status,
        plan_catalogue_status="present" if plans else "missing",
        entitlement_status="present" if entitlements else "missing",
        tenant_access_status="present" if tenant_rules else "missing",
        api_boundary_status="documented" if api_docs else "missing",
        privacy_status="passed" if privacy_ok else "failed",
        staging_status="manual_deployment_required" if staging else "evidence_missing",
        maison_status="contract_review_required" if maison else "evidence_missing",
        scentprint_status="contract_available" if scentprint else "evidence_missing",
        billing_status="intentionally_not_connected", blocking_issues=issues,
        warnings=["This report is not approval for paid launch or customer onboarding."],
        required_operator_actions=["Review proposed plans.", "Complete external legal and commercial review.",
                                   "Approve every onboarding request manually."],
        recommended_next_step="Conduct manual commercial model and legal review; do not take payments.",
        created_at=datetime.now(UTC),
    )
