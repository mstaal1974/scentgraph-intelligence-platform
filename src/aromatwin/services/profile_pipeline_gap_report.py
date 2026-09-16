"""Report code gaps separately from unresolved real-run operator tasks."""

from datetime import UTC, datetime

from aromatwin.schemas.profile_pipeline_rehearsal import (
    ProfilePipelineGapRead,
    ProfilePipelineGapReport,
)


def build_profile_pipeline_gap_report(
    rehearsal_id: str, *, now: datetime | None = None
) -> ProfilePipelineGapReport:
    gaps = [
        ProfilePipelineGapRead(
            gap_id="gap-staging",
            category="manual_operator_step",
            severity="high",
            affected_stage="maison_readiness",
            description="Staging must be configured and smoke-tested before a real handoff.",
            evidence="Rehearsal intentionally performs no deployment or external call.",
            recommended_fix="Configure staging and run reviewed smoke tests.",
            can_fix_automatically=False,
            operator_action_required=True,
            status="open",
        ),
        ProfilePipelineGapRead(
            gap_id="gap-private-input",
            category="manual_operator_step",
            severity="medium",
            affected_stage="supplier_intake",
            description="Real supplier input is absent by design.",
            evidence="Only fictional sample-safe records were rehearsed.",
            recommended_fix="Place authorized files in private runtime storage after rehearsal approval.",
            can_fix_automatically=False,
            operator_action_required=True,
            status="open",
        ),
        ProfilePipelineGapRead(
            gap_id="gap-approval",
            category="missing_review_gate",
            severity="info",
            affected_stage="human_review_gate",
            description="Draft approval remains deliberately unsatisfied.",
            evidence="No rehearsal path may approve a profile.",
            recommended_fix="A human reviewer must assess real drafts in the existing workflow.",
            can_fix_automatically=False,
            operator_action_required=True,
            status="expected",
        ),
    ]
    return ProfilePipelineGapReport(
        rehearsal_id=rehearsal_id,
        overall_status="operator_actions_required",
        gaps=gaps,
        code_gap_count=sum(not g.operator_action_required for g in gaps),
        operator_task_count=sum(g.operator_action_required for g in gaps),
        created_at=now or datetime.now(UTC),
    )
