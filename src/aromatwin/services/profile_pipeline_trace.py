"""Build an identifier-only trace for one fictional candidate."""

from datetime import UTC, datetime

from aromatwin.schemas.profile_pipeline_rehearsal import ProfilePipelineTraceRead

STAGES = [
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


def build_profile_pipeline_trace(
    rehearsal_id: str, candidate_id: str = "fictional-candidate-001", *, now: datetime | None = None
) -> list[ProfilePipelineTraceRead]:
    timestamp = now or datetime.now(UTC)
    rows = []
    for index, stage in enumerate(STAGES):
        next_stage = STAGES[index + 1] if index + 1 < len(STAGES) else None
        status = (
            "human_review_required"
            if stage in {"human_review_gate", "maison_readiness"}
            else "simulated"
        )
        rows.append(
            ProfilePipelineTraceRead(
                trace_id=f"trace-{rehearsal_id}-{index + 1:02d}",
                rehearsal_id=rehearsal_id,
                candidate_id=candidate_id,
                stage_name=stage,
                input_reference=f"ref-{index:02d}",
                output_reference=f"ref-{index + 1:02d}",
                status=status,
                public_safe_summary=f"Fictional candidate completed the {stage} rehearsal check.",
                privacy_status="public_safe",
                next_stage=next_stage,
                blocking_issue="human approval required" if stage == "maison_readiness" else None,
                created_at=timestamp,
            )
        )
    return rows
