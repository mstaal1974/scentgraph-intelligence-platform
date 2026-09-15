from enum import StrEnum
from pydantic import BaseModel, Field


class RecommendationStrategy(StrEnum):
    similarity = "similarity"
    season = "season"
    occasion = "occasion"
    mood = "mood"
    clone_alternative = "clone_alternative"


class RecommendationRequest(BaseModel):
    strategy: RecommendationStrategy = RecommendationStrategy.similarity
    fragrance_id: int | None = None
    season: str | None = None
    occasion: str | None = None
    mood: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class RecommendationItem(BaseModel):
    fragrance_id: int
    score: float = Field(ge=0, le=1)
    reasons: list[str]


class RecommendationResponse(BaseModel):
    strategy: RecommendationStrategy
    status: str
    recommendations: list[RecommendationItem]
