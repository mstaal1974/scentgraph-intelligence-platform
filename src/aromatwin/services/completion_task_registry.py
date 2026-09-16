"""Canonical remaining-task registry; manual work is blocked rather than inferred complete."""

from aromatwin.schemas.platform_completion import CompletionTaskRead

REQUIRED_CATEGORIES = (
    "repository_validation", "privacy_audit", "public_sample_validation",
    "persistence_initialisation", "demo_pilot_run", "private_supplier_intake_preflight",
    "private_supplier_pilot_ready", "profile_generation_ready", "enrichment_ready",
    "review_gates_ready", "launch_intelligence_ready", "operations_api_ready",
    "deployment_readiness", "maison_integration_ready", "consumer_scentprint_ready",
    "micropromote_future_ready", "commercial_packaging_ready",
)


def _task(category: str, *, automatic: bool = True, requirement: str | None = None,
          description: str | None = None) -> CompletionTaskRead:
    status = "ready" if automatic else {
        "private": "blocked_private_data_required",
        "credentials": "blocked_credentials_required",
        "human": "blocked_human_review_required",
        "external": "blocked_external_repo_required",
        "deployment": "blocked_deployment_environment_required",
    }[requirement or "human"]
    label = category.replace("_", " ")
    reason = None if automatic else f"This task requires {requirement} action outside safe automation."
    return CompletionTaskRead(
        task_id=f"completion.{category}", task_name=label.title(), category=category,
        description=description or f"Validate readiness for {label}.",
        can_complete_automatically=automatic,
        requires_private_supplier_files=requirement == "private",
        requires_credentials=requirement == "credentials",
        requires_human_review=requirement == "human",
        requires_external_repository=requirement == "external",
        requires_deployment_environment=requirement == "deployment",
        safe_auto_action=f"Inspect repository evidence for {label}." if automatic else "Report blocker only.",
        blocker_reason=reason, expected_evidence=f"Validated {label} repository evidence.",
        status=status, next_action=(f"Run the safe {label} check." if automatic else reason or "Review."),
    )


def build_completion_task_registry() -> list[CompletionTaskRead]:
    requirements = {
        "private_supplier_pilot_ready": "private",
        "deployment_readiness": "deployment",
        "maison_integration_ready": "external",
        "micropromote_future_ready": "external",
        "commercial_packaging_ready": "human",
    }
    tasks = [_task(category, automatic=category not in requirements,
                   requirement=requirements.get(category)) for category in REQUIRED_CATEGORIES]
    tasks.extend([
        _task("deployment_readiness", automatic=False, requirement="credentials",
              description="Configure production secrets before any deployment."),
        _task("review_gates_ready", automatic=False, requirement="human",
              description="Human profile and compliance approvals remain outstanding."),
    ])
    tasks[-2].task_id = "completion.production_credentials"
    tasks[-2].task_name = "Production Credentials"
    tasks[-1].task_id = "completion.human_approvals"
    tasks[-1].task_name = "Human Approvals"
    return tasks


def public_task(task: CompletionTaskRead) -> dict[str, object]:
    blocker = task.status.removeprefix("blocked_").removesuffix("_required") \
        if task.status.startswith("blocked_") else None
    return {"task_id": task.task_id, "task_name": task.task_name, "category": task.category,
            "status": task.status, "blocker_type": blocker,
            "safe_auto_action": task.safe_auto_action, "next_action": task.next_action,
            "public_safe_summary": task.description}
