"""Build count/status-only acceptance evidence for an internal next step."""

from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.schemas.private_supplier_pilot import PilotAcceptanceReportRead


def build_acceptance_report(run_id: str, stage_results: list[dict[str, object]] | None = None,
                            *, persistence_enabled: bool = False,
                            privacy_passed: bool = True) -> PilotAcceptanceReportRead:
    results = stage_results or []
    by_stage = {str(item.get("stage")): item for item in results}
    count = lambda key: sum(int(item.get(key, 0) or 0) for item in results)  # noqa: E731
    accepted, blocked = count("accepted_count"), count("blocked_count")
    review = count("review_required_count")
    enrichment = count("enrichment_required_count")
    blockers: list[str] = []
    if not privacy_passed:
        status, blockers = "blocked_privacy_risk", ["privacy_audit_failed"]
    elif not results:
        status, blockers = "blocked_missing_inputs", ["no_stage_results"]
    elif blocked:
        status, blockers = "blocked_low_confidence", ["blocked_records_require_review"]
    elif review:
        status = "accepted_for_internal_review"
    elif enrichment:
        status = "accepted_for_profile_enrichment"
    else:
        status = "accepted_for_supplier_review"

    def stage(name: str) -> str:
        return str(by_stage.get(name, {}).get("status", "not_run"))

    actions = (["Resolve privacy blockers before continuing."] if not privacy_passed else
               ["Complete every required human review gate before any external publication."])
    return PilotAcceptanceReportRead(
        acceptance_report_id=f"acceptance-{uuid4().hex[:12]}", run_id=run_id,
        overall_status=status, supplier_import_status=stage("supplier_import"),
        matching_status=stage("supplier_matching"),
        profile_generation_status=stage("bulk_profile_generation"),
        enrichment_queue_status=stage("enrichment_research_queue"),
        launch_intelligence_status=stage("launch_intelligence"),
        review_queue_status=stage("review_queue"),
        persistence_status="enabled" if persistence_enabled else "not_enabled",
        audit_status="passed" if privacy_passed else "failed",
        privacy_status="passed" if privacy_passed else "failed", accepted_count=accepted,
        blocked_count=blocked, review_required_count=review,
        enrichment_required_count=enrichment, supplier_review_required_count=count("supplier_review_required_count"),
        provenance_review_required_count=count("provenance_review_required_count"),
        launch_candidate_count=count("launch_candidate_count"),
        approved_for_next_internal_stage_count=accepted if not blocked else 0,
        critical_blockers=blockers, high_priority_actions=actions,
        recommended_next_step=actions[0], created_at=datetime.now(UTC))


def public_acceptance_report(report: PilotAcceptanceReportRead) -> dict[str, object]:
    return report.model_dump()
