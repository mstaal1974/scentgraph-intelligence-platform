from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EnrichmentReviewStatus(StrEnum):
    enrichment_started = "enrichment_started"
    needs_source_review = "needs_source_review"
    needs_human_review = "needs_human_review"
    ready_for_approval = "ready_for_approval"
    approved_for_catalogue = "approved_for_catalogue"
    rejected_low_confidence = "rejected_low_confidence"
    rejected_licensing_risk = "rejected_licensing_risk"
    rejected_duplicate = "rejected_duplicate"
    requires_more_sources = "requires_more_sources"


class LicensingRisk(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class EnrichmentSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_name: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_url: HttpUrl | None = None
    source_title: str | None = None
    source_domain: str | None = None
    commercial_use_allowed: bool = False
    can_copy_text: bool = False
    can_copy_images: bool = False
    can_use_for_factual_reference: bool = False
    can_use_for_matching: bool = False
    source_confidence: float = Field(default=0, ge=0, le=1)
    notes: str | None = None


class EnrichmentSourceRead(EnrichmentSourceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class EnrichmentReviewCreate(BaseModel):
    profile_draft_id: int
    approved_brand: str
    approved_fragrance_name: str
    official_source_url: HttpUrl | None = None
    source_summary: str | None = None
    description_original: str
    note_pyramid_json: dict[str, list[str]] = Field(default_factory=dict)
    accords_json: list[str] = Field(default_factory=list)
    family: str | None = None
    gender: str | None = None
    season_json: list[str] = Field(default_factory=list)
    occasion_json: list[str] = Field(default_factory=list)
    mood_json: list[str] = Field(default_factory=list)
    scent_vector_json: dict[str, float] = Field(default_factory=dict)
    enrichment_confidence: float = Field(ge=0, le=1)
    licensing_risk: LicensingRisk
    copied_text_detected: bool = False
    review_status: EnrichmentReviewStatus = EnrichmentReviewStatus.needs_human_review


class EnrichmentReviewRead(EnrichmentReviewCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reviewer: str | None = None
    review_notes: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class EnrichmentReviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_summary: str | None = None
    description_original: str | None = None
    note_pyramid_json: dict[str, list[str]] | None = None
    accords_json: list[str] | None = None
    family: str | None = None
    gender: str | None = None
    season_json: list[str] | None = None
    occasion_json: list[str] | None = None
    mood_json: list[str] | None = None
    scent_vector_json: dict[str, float] | None = None
    copied_text_detected: bool | None = None


class ProfileSourceLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enrichment_source_id: int
    usage_type: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    notes: str | None = None


class ProfileSourceLinkRead(ProfileSourceLinkCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_draft_id: int
    created_at: datetime


class EnrichmentDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    rejection_status: EnrichmentReviewStatus | None = None


class EnrichmentGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_draft_ids: list[int] | None = None
