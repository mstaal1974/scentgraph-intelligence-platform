"""Public-safe contracts for the Maison Obsidian internal handoff."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReadinessStatus = Literal[
    "ready_for_maison_contract_review", "ready_for_staging_sync_test",
    "ready_after_private_pilot", "ready_after_human_review",
    "blocked_missing_approved_profiles", "blocked_missing_products",
    "blocked_missing_recommendations", "blocked_privacy_risk",
    "blocked_review_required", "blocked_staging_not_configured",
]
SyncMode = Literal["dry_run", "staging_contract_test", "public_safe_export_only"]


class MaisonIntegrationReadinessReport(BaseModel):
    readiness_id: str
    overall_status: ReadinessStatus
    fragrance_profile_status: str
    product_catalogue_status: str
    variant_status: str
    recommendation_status: str
    scentprint_match_status: str
    bundle_status: str
    review_status: str
    privacy_status: str
    staging_status: str
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    required_operator_actions: list[str] = Field(default_factory=list)
    recommended_next_step: str
    created_at: datetime


class MaisonProductExportRead(BaseModel):
    product_id: str
    fragrance_id: str
    product_slug: str
    product_title: str
    brand_display_name: str
    fragrance_display_name: str
    product_format: str
    size_label: str
    public_description: str
    short_description: str
    scent_family: str
    top_notes: list[str] = Field(default_factory=list)
    heart_notes: list[str] = Field(default_factory=list)
    base_notes: list[str] = Field(default_factory=list)
    accords: list[str] = Field(default_factory=list)
    moods: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    seasons: list[str] = Field(default_factory=list)
    strength_band: str
    longevity_band: str
    projection_band: str
    tags: list[str] = Field(default_factory=list)
    variant_sku: str
    public_price_band: str
    status: str
    review_status: str


class MaisonRecommendationExportRead(BaseModel):
    recommendation_id: str
    source_product_id: str
    recommended_product_id: str
    recommendation_type: str
    match_score_band: str
    reason_summary: str
    shared_notes: list[str] = Field(default_factory=list)
    shared_accords: list[str] = Field(default_factory=list)
    shared_moods: list[str] = Field(default_factory=list)
    public_safe_explanation: str
    status: str


class MaisonScentprintMatchExportRead(BaseModel):
    match_id: str
    scentprint_public_alias: str
    product_id: str
    match_score_band: str
    family_fit: str
    note_fit: str
    mood_fit: str
    occasion_fit: str
    season_fit: str
    reason_summary: str
    confidence_band: str
    review_status: str


class MaisonBundleExportRead(BaseModel):
    bundle_id: str
    bundle_title: str
    bundle_type: str
    product_ids: list[str]
    variant_ids: list[str]
    public_description: str
    bundle_reason: str
    moods: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    seasons: list[str] = Field(default_factory=list)
    status: str
    review_status: str


class MaisonSyncManifestRead(BaseModel):
    sync_manifest_id: str
    sync_mode: SyncMode
    source_environment: str
    target_system_label: str = "Maison Obsidian staging contract"
    generated_at: datetime
    product_count: int
    variant_count: int
    recommendation_count: int
    scentprint_match_count: int
    bundle_count: int
    skipped_count: int
    blocked_count: int
    export_files: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    review_status: str
    privacy_status: str
    blocking_issues: list[str] = Field(default_factory=list)
    recommended_next_action: str


class MaisonSyncManifestPublicSummary(BaseModel):
    sync_manifest_id: str
    sync_mode: SyncMode
    generated_at: datetime
    product_count: int
    variant_count: int
    recommendation_count: int
    scentprint_match_count: int
    bundle_count: int
    skipped_count: int
    blocked_count: int
    review_status: str
    privacy_status: str
    recommended_next_action: str


class MaisonIntegrationAuditReport(BaseModel):
    passed: bool
    audited_file_count: int
    violations: list[str] = Field(default_factory=list)
    privacy_boundary: str = "public_safe_contracts_counts_bands_and_summaries_only"
