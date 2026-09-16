"""Side-effect-free fictional rehearsal of the private profile pipeline."""

from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.schemas.profile_pipeline_rehearsal import (
    ProfilePipelineRehearsalRequest,
    ProfilePipelineRehearsalResult,
)
from aromatwin.services.profile_pipeline_trace import build_profile_pipeline_trace

PIPELINE_STAGES = [
    "supplier_intake",
    "supplier_matching",
    "batch_planning",
    "profile_draft_generation",
    "enrichment_queue",
    "provenance_review",
    "review_packet",
    "human_review_gate",
    "maison_readiness",
    "completion_summary",
]


def run_profile_pipeline_rehearsal(
    request: ProfilePipelineRehearsalRequest, *, now: datetime | None = None
) -> tuple[ProfilePipelineRehearsalResult, list]:
    if request.source_label != "fictional-rehearsal-sample":
        raise ValueError("Only the fictional-rehearsal-sample source is allowed")
    started = now or datetime.now(UTC)
    rehearsal_id = f"rehearsal-{uuid4().hex[:12]}"
    count = request.max_candidates
    trace = build_profile_pipeline_trace(rehearsal_id, now=started)
    trace_only = request.rehearsal_mode == "trace_only"
    result = ProfilePipelineRehearsalResult(
        rehearsal_id=rehearsal_id,
        rehearsal_mode=request.rehearsal_mode,
        source_label=request.source_label,
        started_at=started,
        completed_at=started,
        overall_status="rehearsal_passed_with_warnings",
        stages_run=PIPELINE_STAGES,
        stages_skipped=[],
        stages_failed=[],
        draft_profile_count=0 if trace_only else count,
        enrichment_queue_count=0 if trace_only else count,
        review_packet_count=0 if trace_only else count,
        review_gate_count=0 if trace_only else count,
        maison_ready_count=0,
        blockers=[],
        warnings=[
            "Human approval, staging configuration, and real private intake remain outstanding."
        ],
        recommended_next_action="Configure staging, then perform the authorized private supplier run with human review.",
    )
    return result, trace
