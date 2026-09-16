"""Public-safe contracts for post-deployment staging verification."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, SecretStr

CheckStatus = Literal["passed", "warning", "failed", "skipped"]
SmokeStatus = Literal[
    "staging_smoke_passed",
    "staging_smoke_passed_with_warnings",
    "blocked_unreachable",
    "blocked_auth_failure",
    "blocked_privacy_risk",
    "blocked_readiness_failure",
    "blocked_unknown_failure",
]
HandoffStatus = Literal["complete", "ready", "missing", "blocked", "manual_required"]


class StagingSmokeCheckResult(BaseModel):
    """One sanitized check result; response bodies are deliberately absent."""

    check_name: str
    status: CheckStatus
    http_status: int | None = None
    summary: str
    blocker_type: str | None = None


class StagingSmokeRunRequest(BaseModel):
    """Runtime-only input. SecretStr prevents accidental serialization/repr disclosure."""

    base_url: HttpUrl
    private_api_key: SecretStr | None = Field(default=None, exclude=True, repr=False)
    timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    expected_environment: str = "staging"
    include_openapi_check: bool = False
    include_private_checks: bool = True
    include_cors_check: bool = True


class StagingSmokeRunResult(BaseModel):
    smoke_run_id: str
    base_url_masked: str
    started_at: datetime
    completed_at: datetime
    overall_status: SmokeStatus
    passed_count: int
    warning_count: int
    failed_count: int
    skipped_count: int
    check_results: list[StagingSmokeCheckResult]
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommended_next_action: str


class StagingSmokePublicSummary(BaseModel):
    smoke_run_id: str
    base_url_masked: str
    overall_status: SmokeStatus
    passed_count: int
    warning_count: int
    failed_count: int
    skipped_count: int
    blockers: list[str]
    warnings: list[str]
    recommended_next_action: str


class StagingOperatorHandoffChecklist(BaseModel):
    checklist_id: str
    overall_status: HandoffStatus
    steps: dict[str, HandoffStatus]
    completed_count: int
    manual_required_count: int
    missing_count: int
    blocked_count: int
    recommended_next_action: str


class StagingSmokeAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violation_count: int
    violations: list[str] = Field(default_factory=list)
    summary: str
