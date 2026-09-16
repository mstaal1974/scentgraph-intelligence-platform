"""Public-safe contracts for commercial packaging controls."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

AccessLevel = Literal["public", "authenticated", "internal", "private_operator", "disabled"]
DataScope = Literal["public_safe_only", "tenant_own_data", "anonymised_aggregate", "internal_private", "disabled"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CommercialPlanRead(StrictModel):
    plan_id: str
    plan_name: str
    plan_type: str
    target_customer: str
    included_features: list[str]
    excluded_features: list[str]
    allowed_api_groups: list[str]
    monthly_usage_limits: dict[str, str]
    data_visibility_level: str
    private_workflow_access: bool
    export_access: str
    white_label_allowed: bool
    requires_manual_approval: bool
    billing_integration_status: str
    public_safe_description: str


class CommercialPlanPublicSummary(StrictModel):
    plan_id: str
    plan_name: str
    plan_type: str
    target_customer: str
    included_features: list[str]
    data_visibility_level: str
    white_label_allowed: bool
    requires_manual_approval: bool
    billing_integration_status: str
    public_safe_description: str


class ApiEntitlementRead(StrictModel):
    entitlement_id: str
    plan_id: str
    api_group: str
    allowed: bool
    access_level: AccessLevel
    usage_limit: str
    requires_private_api_key: bool
    requires_human_approval: bool
    public_safe_reason: str
    denial_reason: str | None = None


class ApiEntitlementMatrixRead(StrictModel):
    entitlements: list[ApiEntitlementRead]
    plan_count: int
    api_group_count: int
    privacy_status: str


class TenantFeatureAccessRead(StrictModel):
    tenant_context_id: str
    plan_id: str
    tenant_label: str
    feature_key: str
    allowed: bool
    access_level: AccessLevel
    data_scope: DataScope
    export_allowed: bool
    requires_review: bool
    requires_operator_approval: bool
    denial_reason: str | None = None
    public_safe_summary: str


class TenantFeatureAccessPublicSummary(StrictModel):
    plan_id: str
    feature_key: str
    allowed: bool
    access_level: AccessLevel
    data_scope: DataScope
    export_allowed: bool
    requires_review: bool
    public_safe_summary: str


class CommercialReadinessReport(StrictModel):
    readiness_id: str
    overall_status: str
    plan_catalogue_status: str
    entitlement_status: str
    tenant_access_status: str
    api_boundary_status: str
    privacy_status: str
    staging_status: str
    maison_status: str
    scentprint_status: str
    billing_status: str
    blocking_issues: list[str]
    warnings: list[str]
    required_operator_actions: list[str]
    recommended_next_step: str
    created_at: datetime


class CommercialPackagingAuditReport(StrictModel):
    passed: bool
    audited_file_count: int
    violations: list[str]
    privacy_status: str
