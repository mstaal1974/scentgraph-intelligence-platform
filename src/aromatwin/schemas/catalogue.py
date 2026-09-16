from pydantic import BaseModel, ConfigDict, Field


class CatalogueBrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
    name: str
    slug: str


class CatalogueFragranceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    brand_id: int
    brand: str
    brand_slug: str
    name: str
    slug: str
    concentration: str | None = None
    description: str
    source_confidence: float = Field(ge=0, le=1)
    provenance_summary: str
    provenance_references: tuple[int, ...]
    enrichment_review_id: int


class CatalogueFragranceRead(CatalogueFragranceCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int


class CataloguePromotionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enrichment_review_id: int


class CataloguePromotionDecision(BaseModel):
    accepted: bool
    reason: str


class CataloguePromotionResult(BaseModel):
    decision: CataloguePromotionDecision
    fragrance: CatalogueFragranceRead | None = None
