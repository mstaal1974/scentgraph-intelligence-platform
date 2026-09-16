"""Contracts intentionally limited to bands and aggregated launch intelligence."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReviewStatus = Literal["needs_human_review", "approved", "rejected"]


class LaunchReadinessScoreRead(BaseModel):
    profile_completeness_score: float
    enrichment_confidence_score: float
    supplier_availability_score: float
    source_confidence_score: float
    product_format_readiness_score: float
    margin_suitability_score: float
    seller_demand_score: float
    consumer_interest_score: float
    recommendation_readiness_score: float
    bundle_potential_score: float
    privacy_risk_penalty: float
    provenance_risk_penalty: float
    missing_data_penalty: float
    launch_priority_score: float = Field(ge=0, le=100)
    launch_priority_band: Literal["low", "moderate", "strong", "priority"]
    explanations: list[str]


class LaunchIntelligencePublicSummary(BaseModel):
    launch_candidate_id: str
    fragrance_id: str | None = None
    product_id: str | None = None
    canonical_brand: str
    canonical_fragrance_name: str
    product_title: str | None = None
    profile_status: str
    enrichment_status: str
    catalogue_status: str
    product_status: str
    supplier_availability_band: str
    source_confidence_band: str
    margin_suitability_band: str
    seller_demand_band: str
    consumer_interest_band: str
    recommendation_readiness: str
    bundle_potential_band: str
    format_readiness: str
    launch_priority_score: float
    launch_priority_band: str
    launch_status: str
    launch_reasons: list[str]
    blocking_issues: list[str]
    missing_requirements: list[str]
    recommended_product_formats: list[str]
    recommended_next_action: str
    review_status: ReviewStatus
    created_at: datetime
    updated_at: datetime


class LaunchIntelligenceRead(LaunchIntelligencePublicSummary):
    """Operational projection containing no raw commercial or personal fields."""


class LaunchIntelligencePrivateRead(LaunchIntelligenceRead):
    """Internal IDs are permitted; raw confidential fields remain prohibited."""


class LaunchGapRead(BaseModel):
    gap_id: str
    launch_candidate_id: str
    gap_type: str
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str
    recommended_fix: str
    owner_role: str
    review_status: ReviewStatus


class LaunchGapReport(BaseModel):
    gap_count: int
    gaps: list[LaunchGapRead]
    by_owner_role: dict[str, int] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)


class LaunchRecommendationPlanRead(BaseModel):
    plan_id: str
    plan_theme: str
    candidate_count: int
    recommended_candidates: list[str]
    recommended_formats: list[str]
    rationale: str
    blocking_issues: list[str]
    next_actions: list[str]
    review_status: ReviewStatus


class LaunchRecommendationPlanResult(BaseModel):
    plan_count: int
    plans: list[LaunchRecommendationPlanRead]


class LaunchPriorityReport(BaseModel):
    candidate_count: int
    candidates: list[LaunchIntelligencePublicSummary]


class LaunchIntelligenceAuditReport(BaseModel):
    passed: bool
    candidate_count: int
    violations: list[str]
