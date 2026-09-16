"""Contracts for controlled private-supplier pilot execution."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReadinessStatus = Literal[
    "ready_for_import", "needs_format_mapping", "blocked_unsupported_file_type",
    "blocked_outside_private_path", "blocked_missing_required_columns",
    "blocked_privacy_risk", "skipped_duplicate_file",
]
RunMode = Literal["dry_run", "private_run", "review_only_run"]


class PrivateSupplierIntakeRead(BaseModel):
    intake_id: str
    supplier_public_label: str
    private_source_path: str
    detected_format: str
    file_type: str
    row_count_estimate: int
    header_confidence: str
    detected_private_fields: list[str]
    readiness_status: ReadinessStatus
    blocking_issues: list[str]
    recommended_next_action: str
    created_at: datetime


class PrivateSupplierIntakePublicSummary(BaseModel):
    intake_id: str
    supplier_public_label: str
    detected_format: str
    file_type: str
    row_count_band: str
    header_confidence: str
    readiness_status: ReadinessStatus
    blocker_count: int
    recommended_next_action: str


class PrivateSupplierIntakeResult(BaseModel):
    scanned_count: int
    ready_count: int
    blocked_count: int
    mapping_required_count: int
    items: list[PrivateSupplierIntakePublicSummary]


class PilotExecutionPlanRequest(BaseModel):
    run_id: str | None = None
    run_mode: RunMode = "dry_run"
    supplier_labels: list[str] = Field(default_factory=list)
    selected_stages: list[str] | None = None
    persistence_enabled: bool = False
    audit_enabled: bool = True


class PilotExecutionPlanRead(BaseModel):
    execution_plan_id: str
    run_id: str
    selected_supplier_files: list[str]
    selected_stages: list[str]
    run_mode: RunMode
    expected_outputs: list[str]
    required_review_gates: list[str]
    persistence_enabled: bool
    audit_enabled: bool
    privacy_checks_required: list[str]
    preflight_status: str
    blocking_issues: list[str]
    stage_sequence: list[str]
    rollback_or_recovery_notes: list[str]
    created_at: datetime


class PilotExecutionPlanPublicSummary(BaseModel):
    execution_plan_id: str
    run_id: str
    run_mode: RunMode
    selected_stages: list[str]
    supplier_file_count: int
    required_review_gates: list[str]
    preflight_status: str
    blocker_count: int


class PilotAcceptanceReportRead(BaseModel):
    acceptance_report_id: str
    run_id: str
    overall_status: str
    supplier_import_status: str
    matching_status: str
    profile_generation_status: str
    enrichment_queue_status: str
    launch_intelligence_status: str
    review_queue_status: str
    persistence_status: str
    audit_status: str
    privacy_status: str
    accepted_count: int = 0
    blocked_count: int = 0
    review_required_count: int = 0
    enrichment_required_count: int = 0
    supplier_review_required_count: int = 0
    provenance_review_required_count: int = 0
    launch_candidate_count: int = 0
    approved_for_next_internal_stage_count: int = 0
    critical_blockers: list[str]
    high_priority_actions: list[str]
    recommended_next_step: str
    created_at: datetime


class PilotAcceptancePublicSummary(PilotAcceptanceReportRead):
    """Count/status-only projection; it intentionally contains no source records."""


class PrivatePilotAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violations: list[str]
    configured_input_paths_valid: bool

