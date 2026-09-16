from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class EnrichmentSourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_name: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    source_url: HttpUrl | None = None
    licence_status: str = Field(min_length=1)
    commercial_use_allowed: bool
    source_confidence: float = Field(ge=0, le=1)
    licensing_risk: str = Field(pattern="^(low|medium|high)$")
    reference_only: bool = False


class EnrichmentSourceRead(EnrichmentSourceCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int


class EnrichmentReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_draft_id: int
    brand: str = Field(min_length=1)
    fragrance_name: str = Field(min_length=1)
    concentration: str | None = None
    description_original: str = Field(min_length=1)
    provenance_summary: str = Field(min_length=1)
    source_ids: tuple[int, ...]
    source_confidence: float = Field(ge=0, le=1)
    licensing_risk: str = Field(pattern="^(low|medium|high)$")
    copied_restricted_content: bool = False


class EnrichmentReviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_confidence: float | None = Field(default=None, ge=0, le=1)
    licensing_risk: str | None = Field(default=None, pattern="^(low|medium|high)$")
    copied_restricted_content: bool | None = None


class EnrichmentReviewRead(EnrichmentReviewCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
    review_status: str
    reviewer: str | None = None
    rejection_reason: str | None = None


class EnrichmentReviewGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_draft_id: int
    brand: str = Field(min_length=1)
    fragrance_name: str = Field(min_length=1)
    concentration: str | None = None
    profile_draft_status: str = Field(min_length=1)
    source_ids: tuple[int, ...] = ()


class EnrichmentReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reviewer: str = Field(min_length=1)
    reason: str | None = None
