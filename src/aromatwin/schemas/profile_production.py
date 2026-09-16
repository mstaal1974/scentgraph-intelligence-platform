"""Public-safe contracts for private fragrance profile production."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProfileBatchControls(BaseModel):
    supplier_public_label: str | None = None
    max_profiles: int = Field(default=100, ge=1, le=10_000)
    confidence_threshold: float = Field(default=0.6, ge=0, le=1)
    include_low_confidence: bool = False
    require_match_candidate: bool = True
    require_supplier_intake_ready: bool = True
    include_duplicates: bool = False
    dry_run: bool = True
    output_mode: Literal["private", "public_safe_summary"] = "private"


class ProfileBatchPlanRead(BaseModel):
    batch_plan_id: str
    source_run_id: str
    supplier_public_label: str
    planned_profile_count: int
    skipped_count: int
    blocked_count: int
    duplicate_count: int
    confidence_band_summary: dict[str, int]
    selected_candidate_ids: list[str]
    required_review_gates: list[str]
    required_enrichment_steps: list[str]
    privacy_checks_required: list[str]
    blocking_issues: list[str]
    warnings: list[str]
    recommended_next_action: str
    created_at: datetime


class ProfileBatchPlanPublicSummary(ProfileBatchPlanRead):
    """A plan contains identifiers and counts only, never source values."""


class PrivateProfileDraftRead(BaseModel):
    profile_draft_id: str
    fragrance_candidate_id: str
    supplier_public_label: str
    brand_display_name: str
    fragrance_display_name: str
    inferred_family: str | None = None
    top_notes: list[str] = Field(default_factory=list)
    heart_notes: list[str] = Field(default_factory=list)
    base_notes: list[str] = Field(default_factory=list)
    accords: list[str] = Field(default_factory=list)
    mood_tags: list[str] = Field(default_factory=list)
    occasion_tags: list[str] = Field(default_factory=list)
    season_tags: list[str] = Field(default_factory=list)
    strength_band: str | None = None
    longevity_band: str | None = None
    projection_band: str | None = None
    confidence_band: str
    evidence_status: str
    provenance_status: str
    enrichment_status: str
    review_status: str
    blocking_issues: list[str]
    public_safe_summary: str
    created_at: datetime


class PrivateProfileDraftPublicSummary(BaseModel):
    profile_draft_id: str
    fragrance_candidate_id: str
    supplier_public_label: str
    brand_display_name: str
    fragrance_display_name: str
    confidence_band: str
    evidence_status: str
    provenance_status: str
    enrichment_status: str
    review_status: str
    blocking_issues: list[str]
    public_safe_summary: str
    created_at: datetime


class ProfileProductionRunRequest(BaseModel):
    run_id: str | None = None
    mode: Literal["dry_run", "private_batch_run", "review_packet_only"] = "dry_run"
    controls: ProfileBatchControls = Field(default_factory=ProfileBatchControls)
    intake_manifests: list[dict[str, object]] = Field(default_factory=list)
    match_summaries: list[dict[str, object]] = Field(default_factory=list)


class ProfileProductionRunRead(BaseModel):
    run_id: str
    mode: str
    batch_plan_id: str
    draft_count: int
    enrichment_queue_count: int
    provenance_review_count: int
    review_gate_count: int
    review_packet_count: int
    drafts: list[PrivateProfileDraftPublicSummary]
    status: str
    created_at: datetime


class ProfileProductionReadinessRequest(BaseModel):
    output_path: str = "data/private/runs"
    match_candidate_count: int | None = None
    review_configured: bool = True


class ProfileProductionReadinessReport(BaseModel):
    readiness_id: str
    overall_status: str
    supplier_intake_status: str
    matching_status: str
    profile_generation_status: str
    enrichment_status: str
    review_status: str
    persistence_status: str
    privacy_status: str
    output_path_status: str
    blocking_issues: list[str]
    warnings: list[str]
    required_operator_actions: list[str]
    recommended_next_step: str
    created_at: datetime


class ProfileReviewPacketRequest(BaseModel):
    run_id: str
    profile_draft: PrivateProfileDraftRead


class ProfileReviewPacketRead(BaseModel):
    review_packet_id: str
    run_id: str
    profile_draft_id: str
    fragrance_display_name: str
    brand_display_name: str
    confidence_band: str
    evidence_status: str
    provenance_status: str
    enrichment_status: str
    missing_fields: list[str]
    reviewer_questions: list[str]
    recommended_review_gate: str
    recommended_decision_options: list[str]
    public_safe_summary: str
    created_at: datetime


class ProfileReviewPacketPublicSummary(ProfileReviewPacketRead):
    """Human-review guidance with no supplier-commercial fields."""


class ProfileProductionAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violations: list[str]
    privacy_boundaries: list[str]
