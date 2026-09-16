"""Public-safe contracts for staging deployment diagnostics."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EnvironmentStatus = Literal[
    "ready", "warning", "blocked_missing_secret", "blocked_missing_database",
    "blocked_invalid_storage_path", "blocked_unsafe_cors", "blocked_invalid_environment",
    "not_configured",
]


class EnvironmentVariableCheck(BaseModel):
    name: str
    status: EnvironmentStatus
    masked_value: str
    required: bool = False
    message: str


class EnvironmentReadinessReport(BaseModel):
    environment: str
    overall_status: EnvironmentStatus
    checks: list[EnvironmentVariableCheck]
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class DeploymentReadinessReport(BaseModel):
    deployment_readiness_id: str
    environment: str
    overall_status: str
    environment_status: str
    database_status: str
    migration_status: str
    private_storage_status: str
    public_sample_status: str
    api_health_status: str
    private_workflow_status: str
    audit_status: str
    deployment_template_status: str
    blocking_issues: list[str]
    warnings: list[str]
    required_operator_actions: list[str]
    recommended_next_step: str
    created_at: datetime


class RuntimeHealthRead(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "aromatwin"
    version: str


class RuntimeReadinessRead(BaseModel):
    app_alive: bool
    version_available: bool
    environment_mode: str
    database_configured: bool
    persistence_enabled: bool
    private_storage_configured: bool
    private_storage_path: str | None = None
    review_workflow_available: bool
    private_pilot_available: bool
    platform_completion_available: bool
    audit_scripts_available: bool


class DeploymentAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violation_count: int
    violations: list[str] = Field(default_factory=list)
    summary: str
