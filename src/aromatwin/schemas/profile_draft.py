from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class ProfileDraftStatus(StrEnum):
    needs_human_review = "needs_human_review"
    approved_for_catalogue = "approved_for_catalogue"
    rejected_low_confidence = "rejected_low_confidence"
    rejected_licensing_risk = "rejected_licensing_risk"
    rejected_duplicate = "rejected_duplicate"
    requires_more_sources = "requires_more_sources"


class ProfileDraftBase(BaseModel):
    candidate_brand: str
    candidate_fragrance_name: str
    likely_original_brand: str | None = None
    likely_original_name: str | None = None
    profile_title: str
    description_original: str
    description_generation_method: str
    top_notes_json: list[str] = Field(default_factory=list)
    heart_notes_json: list[str] = Field(default_factory=list)
    base_notes_json: list[str] = Field(default_factory=list)
    accords_json: list[str] = Field(default_factory=list)
    fragrance_family: str | None = None
    gender: str | None = None
    season_json: list[str] = Field(default_factory=list)
    occasion_json: list[str] = Field(default_factory=list)
    mood_json: list[str] = Field(default_factory=list)
    scent_vector_json: dict[str, float] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0, le=1)
    source_confidence: float = Field(ge=0, le=1)
    provenance_notes: str
    restricted_content_detected: bool = False
    review_status: ProfileDraftStatus = ProfileDraftStatus.needs_human_review


class ProfileDraftCreate(ProfileDraftBase):
    supplier_item_id: int
    match_candidate_id: int | None = None


class ProfileDraftRead(ProfileDraftCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reviewer: str | None = None
    rejection_reason: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProfileDraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_title: str | None = None
    description_original: str | None = None
    top_notes_json: list[str] | None = None
    heart_notes_json: list[str] | None = None
    base_notes_json: list[str] | None = None
    accords_json: list[str] | None = None
    fragrance_family: str | None = None
    gender: str | None = None
    season_json: list[str] | None = None
    occasion_json: list[str] | None = None
    mood_json: list[str] | None = None
    scent_vector_json: dict[str, float] | None = None
    provenance_notes: str | None = None
    source_confidence: float | None = Field(default=None, ge=0, le=1)


class ProfileDraftGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    supplier_item_ids: list[int] | None = None
    match_candidate_ids: list[int] | None = None


class ProfileDraftDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    rejection_status: ProfileDraftStatus | None = None
