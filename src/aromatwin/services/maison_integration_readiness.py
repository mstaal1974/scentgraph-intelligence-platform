"""Evidence-driven, side-effect-free Maison handoff readiness checks."""

from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.schemas.maison_integration import MaisonIntegrationReadinessReport


def check_maison_integration_readiness(
    *, approved_profile_count: int = 0, approved_product_count: int = 0,
    supported_variant_count: int = 0, public_copy_count: int = 0,
    recommendation_count: int = 0, scentprint_contract_count: int = 0,
    bundle_count: int = 0, launch_stage_approved: bool = False,
    review_gates_satisfied: bool = False, privacy_audit_passed: bool = True,
    supplier_commercial_fields_present: bool = False,
    copied_third_party_content_present: bool = False, staging_api_ready: bool = False,
) -> MaisonIntegrationReadinessReport:
    """Assess internal handoff evidence without reading private values or contacting a system."""
    statuses = {
        "fragrance_profile_status": "approved" if approved_profile_count else "missing",
        "product_catalogue_status": "approved" if approved_product_count else "missing",
        "variant_status": "available" if supported_variant_count else "missing",
        "recommendation_status": "available" if recommendation_count else "missing",
        "scentprint_match_status": "available" if scentprint_contract_count else "missing",
        "bundle_status": "available" if bundle_count else "missing",
        "review_status": "satisfied" if review_gates_satisfied else "human_review_required",
        "privacy_status": "passed" if privacy_audit_passed and not supplier_commercial_fields_present
        and not copied_third_party_content_present else "failed",
        "staging_status": "ready" if staging_api_ready else "not_configured",
    }
    blockers = []
    actions = []
    if not approved_profile_count:
        blockers.append("Approved fragrance profiles are missing.")
        actions.append("Complete profile approval through the existing human review workflow.")
        overall = "blocked_missing_approved_profiles"
    elif not approved_product_count or not supported_variant_count or public_copy_count < approved_product_count:
        blockers.append("Approved products, supported variants, or public-safe copy are missing.")
        actions.append("Complete and review the approved product catalogue evidence.")
        overall = "blocked_missing_products"
    elif not recommendation_count or not scentprint_contract_count or not bundle_count:
        blockers.append("Recommendation, Scentprint match, or bundle evidence is missing.")
        actions.append("Generate and review the missing public-safe contract records.")
        overall = "blocked_missing_recommendations"
    elif statuses["privacy_status"] == "failed":
        blockers.append("Privacy or provenance audit did not pass.")
        actions.append("Remove unsafe fields or content and rerun the Maison privacy audit.")
        overall = "blocked_privacy_risk"
    elif not review_gates_satisfied or not launch_stage_approved:
        blockers.append("Human review and next internal-stage approval are required.")
        actions.append("Obtain recorded human approval for the internal handoff only.")
        overall = "blocked_review_required"
    elif not staging_api_ready:
        blockers.append("Staging API readiness is not configured.")
        actions.append("Configure and validate the staging API before a contract sync test.")
        overall = "blocked_staging_not_configured"
    else:
        overall = "ready_for_staging_sync_test"
        actions.append("Run a reviewed staging contract test; do not publish products.")
    warnings = ["Approval means internal handoff readiness, never public launch."]
    return MaisonIntegrationReadinessReport(
        readiness_id=f"maison-readiness-{uuid4().hex[:12]}", overall_status=overall,
        blocking_issues=blockers, warnings=warnings, required_operator_actions=actions,
        recommended_next_step=actions[0], created_at=datetime.now(UTC), **statuses,
    )


class MaisonIntegrationReadinessService:
    check = staticmethod(check_maison_integration_readiness)
