"""Preflight planning for a private supplier pilot."""

import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aromatwin.schemas.private_supplier_pilot import (
    PilotExecutionPlanRead,
    PilotExecutionPlanRequest,
    PrivateSupplierIntakeRead,
)

STAGES = ("supplier_import", "supplier_matching", "supplier_sourcing", "margin_scenarios",
          "bulk_profile_generation", "profile_coverage", "enrichment_research_queue",
          "launch_intelligence", "review_queue", "persistence", "audit")
REVIEW_GATES = ("supplier_match_review", "profile_provenance_review",
                "launch_readiness_review", "final_internal_review")
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def build_execution_plan(
    request: PilotExecutionPlanRequest | dict[str, object],
    intake: list[PrivateSupplierIntakeRead] | None = None,
) -> PilotExecutionPlanRead:
    req = request if isinstance(request, PilotExecutionPlanRequest) else PilotExecutionPlanRequest(**request)
    run_id = req.run_id or f"private-pilot-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
    if not _RUN_ID.fullmatch(run_id):
        raise ValueError("run_id contains unsupported characters")
    selected = list(req.selected_stages or STAGES)
    unknown = sorted(set(selected) - set(STAGES))
    if unknown:
        raise ValueError(f"Unknown stages: {', '.join(unknown)}")
    selected = list(dict.fromkeys(selected))
    if req.run_mode == "review_only_run":
        selected = [stage for stage in selected if stage not in {"supplier_import", "supplier_matching"}]
        if "review_queue" not in selected:
            selected.insert(0, "review_queue")
    items = [item for item in (intake or []) if not req.supplier_labels
             or item.supplier_public_label in req.supplier_labels]
    files = [item.private_source_path for item in items if item.readiness_status == "ready_for_import"]
    blockers = [f"intake:{item.readiness_status}" for item in items
                if item.readiness_status != "ready_for_import"]
    if req.run_mode != "review_only_run" and not files:
        blockers.append("no_ready_supplier_inputs")
    outputs = [] if req.run_mode == "dry_run" else [f"data/private/runs/{run_id}/"]
    return PilotExecutionPlanRead(
        execution_plan_id=f"plan-{uuid4().hex[:12]}", run_id=run_id,
        selected_supplier_files=files, selected_stages=selected, run_mode=req.run_mode,
        expected_outputs=outputs, required_review_gates=list(REVIEW_GATES),
        persistence_enabled=req.persistence_enabled, audit_enabled=req.audit_enabled,
        privacy_checks_required=["private_path_boundary", "public_projection", "tracked_file_audit"],
        preflight_status="blocked" if blockers else "ready", blocking_issues=blockers,
        stage_sequence=selected,
        rollback_or_recovery_notes=["No automatic approval or publication is permitted.",
            "Remove the private run directory and rerun from reviewed inputs after a failure."],
        created_at=datetime.now(UTC),
    )


def public_execution_plan(plan: PilotExecutionPlanRead) -> dict[str, object]:
    return {"execution_plan_id": plan.execution_plan_id, "run_id": plan.run_id,
            "run_mode": plan.run_mode, "selected_stages": plan.selected_stages,
            "supplier_file_count": len(plan.selected_supplier_files),
            "required_review_gates": plan.required_review_gates,
            "preflight_status": plan.preflight_status, "blocker_count": len(plan.blocking_issues)}


def assert_private_output(path: Path, data_root: Path = Path("data")) -> None:
    private_runs = (data_root.resolve() / "private" / "runs")
    if not path.resolve().is_relative_to(private_runs):
        raise ValueError("Operational output must remain under data/private/runs/")

