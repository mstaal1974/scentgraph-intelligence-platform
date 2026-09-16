from pydantic import BaseModel, ConfigDict, Field


class MatchCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    supplier_item_id: int
    candidate_brand: str
    candidate_fragrance_name: str
    candidate_concentration: str | None = None
    candidate_source_type: str
    candidate_source_reference: str | None = None
    match_method: str
    match_confidence: float = Field(ge=0, le=1)
    match_notes: str | None = None
    review_status: str


class MatchCandidateGenerateRequest(BaseModel):
    supplier_item_id: int
    candidate_brand: str
    candidate_fragrance_name: str
    candidate_concentration: str | None = None
    candidate_source_type: str = "manual"
    candidate_source_reference: str | None = None
    match_method: str = "manual"
    match_confidence: float = Field(ge=0, le=1)
