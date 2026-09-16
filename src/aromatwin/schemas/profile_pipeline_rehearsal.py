"""Public-safe contracts for the fictional profile-pipeline rehearsal."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RehearsalMode = Literal["dry_rehearsal", "sample_private_rehearsal", "trace_only"]
OverallStatus = Literal[
    "rehearsal_passed",
    "rehearsal_passed_with_warnings",
    "blocked_missing_module",
    "blocked_integration_gap",
    "blocked_privacy_risk",
    "blocked_validation_failure",
    "blocked_unknown_failure",
]


class ProfilePipelineRehearsalRequest(BaseModel):
    rehearsal_mode: RehearsalMode = "dry_rehearsal"
    max_candidates: int = Field(default=1, ge=1, le=25)
    source_label: str = "fictional-rehearsal-sample"


class ProfilePipelineStageResult(BaseModel):
    stage_name: str
    status: str
    record_count: int = 0
    public_safe_summary: str


class ProfilePipelineRehearsalResult(BaseModel):
    rehearsal_id: str
    rehearsal_mode: RehearsalMode
    source_label: str
    started_at: datetime
    completed_at: datetime
    overall_status: OverallStatus
    stages_run: list[str]
    stages_skipped: list[str]
    stages_failed: list[str]
    draft_profile_count: int
    enrichment_queue_count: int
    review_packet_count: int
    review_gate_count: int
    maison_ready_count: int
    blockers: list[str]
    warnings: list[str]
    recommended_next_action: str


class ProfilePipelineTraceRead(BaseModel):
    trace_id: str
    rehearsal_id: str
    candidate_id: str
    stage_name: str
    input_reference: str
    output_reference: str
    status: str
    public_safe_summary: str
    privacy_status: str
    next_stage: str | None
    blocking_issue: str | None
    created_at: datetime


class ProfilePipelineGapRead(BaseModel):
    gap_id: str
    category: str
    severity: str
    affected_stage: str
    description: str
    evidence: str
    recommended_fix: str
    can_fix_automatically: bool
    operator_action_required: bool
    status: str


class ProfilePipelineGapReport(BaseModel):
    rehearsal_id: str
    overall_status: str
    gaps: list[ProfilePipelineGapRead]
    code_gap_count: int
    operator_task_count: int
    created_at: datetime


class ProfilePipelineRehearsalPublicSummary(ProfilePipelineRehearsalResult):
    """Counts, statuses and a fictional label only."""


class ProfilePipelineRehearsalAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violations: list[str]
    privacy_boundaries: list[str]
