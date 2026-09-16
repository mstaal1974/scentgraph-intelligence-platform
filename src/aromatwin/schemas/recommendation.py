from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RecommendationType = Literal[
    "similar_fragrance",
    "same_family",
    "same_mood",
    "same_occasion",
    "same_season",
    "contrast_pick",
    "softer_alternative",
    "stronger_alternative",
    "clone_or_inspired_by_candidate",
    "discovery_pick",
]


class RecommendationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_fragrance_id: int
    recommended_fragrance_id: int
    recommendation_type: RecommendationType
    score: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)
    shared_dimensions_json: dict[str, object] = Field(default_factory=dict)
    difference_summary: str
    confidence_score: float = Field(ge=0, le=1)
    generation_method: str
    review_status: str = "needs_human_review"


class RecommendationRead(RecommendationCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    rejection_reason: str | None = None


class RecommendationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendation_type: RecommendationType | None = None
    reason: str | None = Field(default=None, min_length=1)
    difference_summary: str | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    review_status: str | None = None


class RecommendationGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_fragrance_id: int
    limit: int = Field(default=10, ge=1, le=100)


class SimilarFragranceRequest(RecommendationGenerateRequest):
    minimum_score: float = Field(default=0, ge=0, le=1)


class ContextualRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mood: str | None = None
    occasion: str | None = None
    season: str | None = None
    family: str | None = None
    intensity: float | None = Field(default=None, ge=0, le=1)
    limit: int = Field(default=10, ge=1, le=100)


class RecommendationResult(BaseModel):
    fragrance_id: int
    score: float = Field(ge=0, le=1)
    reason: str
    recommendation: RecommendationRead | None = None


class RecommendationDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = None
