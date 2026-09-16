"""Public-safe contracts for the internal bulk profile workflow."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BulkProfileGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    private_offer_path: str | None = None
    private_match_candidate_path: str | None = None
    private_existing_draft_path: str | None = None


class BulkProfileDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    profile_draft_id: str
    supplier_offer_ids: list[str]
    match_candidate_ids: list[str]
    canonical_brand: str
    canonical_fragrance_name: str
    concentration: str | None = None
    candidate_reference: str | None = None
    draft_description: str
    provenance_notes: str
    source_confidence: float = Field(ge=0, le=1)
    confidence_reason: str
    missing_profile_fields: list[str]
    enrichment_needed: bool
    review_status: str
    created_at: datetime
    updated_at: datetime


class BulkProfileDraftPublicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    profile_draft_id: str
    canonical_brand: str
    canonical_fragrance_name: str
    concentration: str | None = None
    draft_description: str
    provenance_notes: str
    source_confidence: float = Field(ge=0, le=1)
    confidence_reason: str
    missing_profile_fields: list[str]
    enrichment_needed: bool
    review_status: str
    created_at: datetime
    updated_at: datetime


class BulkProfileGenerationResult(BaseModel):
    accepted_count: int
    rejected_count: int
    unique_candidate_count: int
    skipped_duplicate_count: int
    drafts: list[BulkProfileDraftPublicSummary]


class ProfileCoverageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    canonical_brand: str
    canonical_fragrance_name: str
    supplier_count: int
    supplier_offer_count: int
    has_match_candidate: bool
    has_profile_draft: bool
    has_enrichment_review: bool
    has_catalogue_record: bool
    has_scent_vector: bool
    has_recommendations: bool
    profile_status: str
    source_confidence: float | None = None
    missing_fields: list[str]
    next_action: str


class ProfileCoverageReport(BaseModel):
    total_fragrance_candidates: int
    status_counts: dict[str, int]
    records: list[ProfileCoverageRead] = Field(default_factory=list)


class EnrichmentResearchQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    queue_id: str
    profile_draft_id: str | None = None
    canonical_brand: str
    canonical_fragrance_name: str
    priority: int = Field(ge=0, le=100)
    missing_fields: list[str]
    suggested_source_types: list[str]
    research_questions: list[str]
    licensing_risk: str
    review_status: str
    next_action: str


class EnrichmentResearchQueueResult(BaseModel):
    item_count: int
    items: list[EnrichmentResearchQueueItem]


class ProfileGenerationAuditReport(BaseModel):
    draft_count: int
    coverage_count: int
    research_queue_count: int
    all_require_human_review: bool
    catalogue_records_generated: int = 0
    private_commercial_fields_exposed: bool = False
    copied_third_party_content_stored: bool = False
    details: dict[str, Any] = Field(default_factory=dict)
