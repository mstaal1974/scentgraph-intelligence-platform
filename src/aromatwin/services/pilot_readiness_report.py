"""Derive a conservative, public-safe pilot recommendation from stage evidence."""


def build_readiness_report(run_id: str, stages: list[dict[str, object]],
                           privacy_audit_status: str = "passed") -> dict[str, object]:
    by_name = {str(item["stage"]): item for item in stages}
    blockers = [item for stage in stages for item in stage.get("blockers", [])]
    critical = [item for item in blockers if item["severity"] == "critical"]
    high = [item for item in blockers if item["severity"] == "high"]
    skipped = {name for name, item in by_name.items() if item["status"] == "skipped"}
    failed = {name for name, item in by_name.items() if item["status"] == "failed"}
    completed = {name for name, item in by_name.items() if item["status"] == "completed"}

    if privacy_audit_status != "passed":
        status = "blocked_privacy_risk"
    elif critical or failed:
        status = "blocked_low_confidence"
    elif skipped & {"supplier_import", "bulk_profile_generation", "launch_intelligence"}:
        status = "blocked_missing_inputs"
    elif "enrichment_research_queue" in skipped:
        status = "ready_after_enrichment"
    elif "supplier_matching" in skipped:
        status = "ready_after_supplier_review"
    elif "product_catalogue_readiness" in skipped:
        status = "ready_after_product_setup"
    elif "launch_intelligence" in completed:
        status = "ready_for_small_launch_pilot"
    else:
        status = "ready_for_private_review"

    actions = list(dict.fromkeys(item["recommended_fix"] for item in blockers))[:5]
    if not actions:
        actions = ["Complete human admin review before any launch decision."]
    def stage_status(name: str) -> str:
        return str(by_name.get(name, {}).get("status", "not_requested"))

    launch_now = 1 if status == "ready_for_small_launch_pilot" else 0
    return {
        "run_id": run_id, "readiness_status": status,
        "supplier_import_status": stage_status("supplier_import"),
        "profile_generation_status": stage_status("bulk_profile_generation"),
        "enrichment_queue_status": stage_status("enrichment_research_queue"),
        "catalogue_readiness_status": stage_status("catalogue_readiness"),
        "product_readiness_status": stage_status("product_catalogue_readiness"),
        "recommendation_readiness_status": stage_status("recommendation_readiness"),
        "launch_intelligence_status": stage_status("launch_intelligence"),
        "privacy_audit_status": privacy_audit_status, "critical_blockers": critical,
        "high_priority_gaps": high, "launch_now_count": launch_now,
        "enrichment_needed_count": int(status == "ready_after_enrichment"),
        "supplier_review_needed_count": int(status == "ready_after_supplier_review"),
        "product_setup_needed_count": int(status == "ready_after_product_setup"),
        "hold_count": int(status.startswith("blocked_")), "top_next_actions": actions,
        "pilot_recommendation": (
            "Eligible for a small private pilot after explicit human review; this is not public "
            "launch approval." if launch_now else "Resolve the listed gates and complete human review."
        ),
    }
