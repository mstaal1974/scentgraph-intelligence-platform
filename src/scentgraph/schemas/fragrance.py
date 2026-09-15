from pydantic import BaseModel, ConfigDict, Field


class FragranceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int
    name: str
    slug: str
    concentration: str | None = None
    description: str | None = None
    family: str | None = None
    gender: str | None = None
    release_year: int | None = Field(default=None, ge=1700, le=2200)
    perfumer: str | None = None
    verified: bool = False
    source_confidence: float = Field(ge=0, le=1)


class SearchResult(BaseModel):
    entity_type: str
    id: int
    name: str
    score: float = Field(ge=0, le=1)


class SimilarityMatch(BaseModel):
    fragrance_id: int
    score: float = Field(ge=0, le=1)
    reason: str


class CloneMatch(BaseModel):
    fragrance_id: int
    relationship_type: str
    similarity_score: float | None = Field(default=None, ge=0, le=1)
