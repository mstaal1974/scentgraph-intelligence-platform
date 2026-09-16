"""Public-safe contracts for the final repository completion control plane."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CompletionStatus = Literal[
    "completed", "ready", "blocked_private_data_required", "blocked_credentials_required",
    "blocked_human_review_required", "blocked_external_repo_required",
    "blocked_deployment_environment_required", "failed", "not_applicable",
]
FinalPlatformStatus = Literal[
    "repository_complete_ready_for_private_data", "ready_for_private_supplier_pilot",
    "ready_after_private_supplier_files_added", "ready_after_credentials_configured",
    "ready_after_human_review", "blocked_privacy_risk", "blocked_missing_core_module",
    "blocked_validation_failure",
]


class CompletionTaskRead(BaseModel):
    task_id: str
    task_name: str
    category: str
    description: str
    can_complete_automatically: bool
    requires_private_supplier_files: bool = False
    requires_credentials: bool = False
    requires_human_review: bool = False
    requires_external_repository: bool = False
    requires_deployment_environment: bool = False
    safe_auto_action: str
    blocker_reason: str | None = None
    expected_evidence: str
    status: CompletionStatus
    next_action: str


class CompletionTaskPublicSummary(BaseModel):
    task_id: str
    task_name: str
    category: str
    status: CompletionStatus
    blocker_type: str | None = None
    safe_auto_action: str
    next_action: str
    public_safe_summary: str


class PlatformCompletionRequest(BaseModel):
    demo_mode: bool = False
    run_audits: bool = True
    export_report: bool = False


class CompletionBlockerRead(BaseModel):
    task_id: str
    blocker_type: str
    summary: str
    next_action: str


class PlatformCompletionResult(BaseModel):
    completion_run_id: str
    started_at: datetime
    completed_at: datetime
    total_tasks: int
    completed_count: int
    ready_count: int
    blocked_count: int
    failed_count: int
    automatic_actions_completed: list[str]
    manual_actions_required: list[str]
    privacy_audit_status: str
    deployment_readiness_status: str
    private_pilot_readiness_status: str
    final_platform_status: FinalPlatformStatus
    blockers: list[CompletionBlockerRead] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)


class CompletionReadinessReport(BaseModel):
    generated_at: datetime
    final_platform_status: FinalPlatformStatus
    sections: dict[str, list[CompletionTaskPublicSummary]]
    safe_to_run_now: list[CompletionTaskPublicSummary]
    requires_private_supplier_files: list[CompletionTaskPublicSummary]
    requires_api_keys_or_secrets: list[CompletionTaskPublicSummary]
    requires_human_review: list[CompletionTaskPublicSummary]
    requires_deployment: list[CompletionTaskPublicSummary]
    requires_external_website_repository_work: list[CompletionTaskPublicSummary]
    future_commercial_enhancement: list[CompletionTaskPublicSummary]
    remaining_manual_tasks: list[str]


class CompletionAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violations: list[str]
    privacy_boundary: str = "public_safe_status_and_counts_only"
