from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EnrichmentReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    match_candidate_id: int
    approved_brand: str
    approved_fragrance_name: str
    official_source_url: HttpUrl | None = None
    description_original: str | None = None
    description_ai_generated: bool = False
    description_reviewed: bool = False
    review_status: str
    reviewer: str | None = None
    approved_at: datetime | None = None
    source_confidence: float = Field(ge=0, le=1)


class ReviewDecisionRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    reason: str | None = None
