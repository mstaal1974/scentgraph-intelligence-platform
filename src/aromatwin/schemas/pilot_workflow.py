"""Public-safe contracts for the private pilot orchestration boundary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RunMode = Literal["dry_run", "private_run", "demo_sample"]
StageStatus = Literal["completed", "skipped", "failed"]


class PilotBlockerRead(BaseModel):
    blocker_type: str
    severity: Literal["low", "medium", "high", "critical"]
    stage: str
    owner_role: str
    summary: str
    recommended_fix: str


class PilotWorkflowStageResult(BaseModel):
    stage: str
    status: StageStatus
    accepted_count: int = 0
    skipped_count: int = 0
    blocked_count: int = 0
    warning_count: int = 0
    summary: str
    blockers: list[PilotBlockerRead] = Field(default_factory=list)


class PilotWorkflowRequest(BaseModel):
    run_id: str | None = None
    run_mode: RunMode = "dry_run"
    stages: list[str] | None = None
    input_locations: list[str] = Field(default_factory=list)
    source_input_type: str = "private_files"
    source_input_label: str = "private pilot input"


class PilotWorkflowResult(BaseModel):
    run_id: str
    run_mode: RunMode
    started_at: datetime
    completed_at: datetime
    stage_results: list[PilotWorkflowStageResult]
    input_locations: list[str]
    output_locations: list[str]
    accepted_count: int
    skipped_count: int
    blocked_count: int
    warning_count: int
    privacy_audit_status: str
    readiness_status: str
    next_actions: list[str]


class PilotRunManifestRead(BaseModel):
    run_id: str
    run_mode: RunMode
    source_input_type: str
    source_input_label: str
    private_input_paths: list[str]
    private_output_paths: list[str]
    public_sample_output_paths: list[str]
    stages_requested: list[str]
    stages_completed: list[str]
    stages_skipped: list[str]
    stages_failed: list[str]
    audit_results: dict[str, str]
    privacy_boundary_notes: list[str]
    blocking_issues: list[PilotBlockerRead]
    generated_artifacts: list[str]
    created_at: datetime
    updated_at: datetime


class PilotRunManifestPublicSummary(BaseModel):
    run_id: str
    run_mode: RunMode
    completed_count: int
    skipped_count: int
    failed_count: int
    blocker_count: int
    privacy_audit_status: str
    readiness_status: str


class PilotReadinessReportRead(BaseModel):
    run_id: str
    readiness_status: str
    supplier_import_status: str
    profile_generation_status: str
    enrichment_queue_status: str
    catalogue_readiness_status: str
    product_readiness_status: str
    recommendation_readiness_status: str
    launch_intelligence_status: str
    privacy_audit_status: str
    critical_blockers: list[PilotBlockerRead]
    high_priority_gaps: list[PilotBlockerRead]
    launch_now_count: int = 0
    enrichment_needed_count: int = 0
    supplier_review_needed_count: int = 0
    product_setup_needed_count: int = 0
    hold_count: int = 0
    top_next_actions: list[str]
    pilot_recommendation: str


class PilotReadinessPublicSummary(PilotReadinessReportRead):
    """The readiness report is deliberately count/status-only and public-safe."""


class PilotWorkflowAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violations: list[str]
    operational_output_status: str
