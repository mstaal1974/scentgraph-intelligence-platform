from pydantic import BaseModel, Field, field_validator

from aromatwin.models.scent_vector import VECTOR_DIMENSIONS


class ScentprintRequest(BaseModel):
    preferences: dict[str, float]
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, value: dict[str, float]) -> dict[str, float]:
        unknown = set(value) - set(VECTOR_DIMENSIONS)
        if unknown:
            raise ValueError(f"Unknown scent dimensions: {', '.join(sorted(unknown))}")
        if not value or any(score < 0 or score > 1 for score in value.values()):
            raise ValueError("Provide scores between 0 and 1")
        return value


class ScentprintResponse(BaseModel):
    vector: dict[str, float]
    algorithm: str = "cosine_similarity"
    matches: list[dict[str, object]]
