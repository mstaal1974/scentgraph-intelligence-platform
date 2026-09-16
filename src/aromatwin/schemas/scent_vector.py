from pydantic import BaseModel, ConfigDict, Field


class ScentDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    warm: float = Field(ge=0, le=1)
    fresh: float = Field(ge=0, le=1)
    sweet: float = Field(ge=0, le=1)
    dark: float = Field(ge=0, le=1)
    woody: float = Field(ge=0, le=1)
    floral: float = Field(ge=0, le=1)
    spicy: float = Field(ge=0, le=1)
    fruity: float = Field(ge=0, le=1)
    green: float = Field(ge=0, le=1)
    aquatic: float = Field(ge=0, le=1)
    marine: float = Field(ge=0, le=1)
    leather: float = Field(ge=0, le=1)
    powdery: float = Field(ge=0, le=1)
    resinous: float = Field(ge=0, le=1)
    smoky: float = Field(ge=0, le=1)
    gourmand: float = Field(ge=0, le=1)
    citrus: float = Field(ge=0, le=1)
    aromatic: float = Field(ge=0, le=1)
    amber: float = Field(ge=0, le=1)
    musky: float = Field(ge=0, le=1)
    luxury: float = Field(ge=0, le=1)
    projection: float = Field(ge=0, le=1)
    longevity: float = Field(ge=0, le=1)


class ScentVectorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fragrance_id: int
    values: ScentDimensions
    confidence_score: float = Field(ge=0, le=1)
    generation_method: str
    review_status: str = "needs_human_review"
    provenance_references: tuple[int, ...]
    source_fingerprint: str


class ScentVectorRead(ScentVectorCreate):
    id: int
    rejection_reason: str | None = None


class ScentVectorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: ScentDimensions | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    review_status: str | None = None


class ScentVectorGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fragrance_id: int


class ScentVectorSimilarityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scent_vector_id: int
    candidate_vector_ids: tuple[int, ...] = ()


class ScentVectorSimilarityResult(BaseModel):
    scent_vector_id: int
    candidate_vector_id: int
    fragrance_id: int
    similarity_score: float = Field(ge=0, le=1)


class ScentVectorReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = None
