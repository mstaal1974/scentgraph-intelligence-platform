from pydantic import BaseModel, ConfigDict, Field


class ProfileDraftCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_item_id: int
    match_candidate_id: int
    brand: str = Field(min_length=1)
    fragrance_name: str = Field(min_length=1)
    concentration: str | None = None
    description: str = Field(min_length=1)
    provenance_notes: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_confidence: float = Field(ge=0, le=1)


class ProfileDraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str | None = Field(default=None, min_length=1)
    fragrance_name: str | None = Field(default=None, min_length=1)
    concentration: str | None = None
    description: str | None = Field(default=None, min_length=1)
    provenance_notes: str | None = Field(default=None, min_length=1)
    source_confidence: float | None = Field(default=None, ge=0, le=1)


class ProfileDraftRead(ProfileDraftCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    review_status: str
    rejection_reason: str | None = None


class ProfileDraftGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_item_id: int
    match_candidate_id: int
    supplier_brand: str = Field(min_length=1)
    supplier_name: str = Field(min_length=1)
    candidate_brand: str = Field(min_length=1)
    candidate_fragrance_name: str = Field(min_length=1)
    candidate_concentration: str | None = None
    candidate_source_type: str = Field(min_length=1)
    candidate_source_reference: str | None = None
    match_confidence: float = Field(ge=0, le=1)


class ProfileDraftDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer: str = Field(min_length=1)
    reason: str | None = None
