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
    limit: int = Field(default=10, ge=1, le=100)


class RecommendationResponse(BaseModel):
    strategy: RecommendationStrategy
    status: str
    recommendations: list[dict[str, object]]
