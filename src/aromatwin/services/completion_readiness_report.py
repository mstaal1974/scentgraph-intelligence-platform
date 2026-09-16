"""Build a status-only completion report without operational or personal records."""

from datetime import UTC, datetime

from aromatwin.schemas.platform_completion import CompletionReadinessReport, CompletionTaskRead
from aromatwin.services.completion_task_registry import public_task

SECTION_BY_CATEGORY = {
    "repository_validation": "core platform modules", "operations_api_ready": "core platform modules",
    "privacy_audit": "data privacy controls", "public_sample_validation": "data privacy controls",
    "private_supplier_intake_preflight": "supplier workflow readiness",
    "profile_generation_ready": "profile workflow readiness", "enrichment_ready": "profile workflow readiness",
    "review_gates_ready": "review workflow readiness",
    "persistence_initialisation": "persistence and audit readiness",
    "demo_pilot_run": "private pilot readiness", "private_supplier_pilot_ready": "private pilot readiness",
    "deployment_readiness": "deployment readiness", "maison_integration_ready": "Maison integration readiness",
    "consumer_scentprint_ready": "consumer Scentprint readiness",
    "micropromote_future_ready": "future MicroPromote readiness",
    "commercial_packaging_ready": "remaining manual tasks",
    "launch_intelligence_ready": "core platform modules",
}


def build_readiness_report(tasks: list[CompletionTaskRead], final_status: str):
    summaries = [(task, public_task(task)) for task in tasks]
    sections: dict[str, list[dict[str, object]]] = {}
    for task, summary in summaries:
        sections.setdefault(SECTION_BY_CATEGORY[task.category], []).append(summary)
    def select(predicate):
        return [summary for task, summary in summaries if predicate(task)]
    return CompletionReadinessReport(
        generated_at=datetime.now(UTC), final_platform_status=final_status, sections=sections,
        safe_to_run_now=select(lambda t: t.status in {"completed", "ready"}),
        requires_private_supplier_files=select(lambda t: t.requires_private_supplier_files),
        requires_api_keys_or_secrets=select(lambda t: t.requires_credentials),
        requires_human_review=select(lambda t: t.requires_human_review),
        requires_deployment=select(lambda t: t.requires_deployment_environment),
        requires_external_website_repository_work=select(lambda t: t.requires_external_repository),
        future_commercial_enhancement=select(lambda t: t.category in {
            "micropromote_future_ready", "commercial_packaging_ready"}),
        remaining_manual_tasks=[t.next_action for t in tasks if t.status.startswith("blocked_")],
    )
