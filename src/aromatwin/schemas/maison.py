"""Public contract consumed by Maison Obsidian and other licensed retailers."""

from pydantic import BaseModel, ConfigDict, Field


class MaisonScentVectorSummary(BaseModel):
    dimensions: dict[str, float] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0, le=1)
    review_status: str


class MaisonFragranceCard(BaseModel):
    id: int
    slug: str
    title: str
    brand: str
    family: str | None = None
    accords: list[str] = Field(default_factory=list)
    mood: list[str] = Field(default_factory=list)
    occasion: list[str] = Field(default_factory=list)
    season: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    review_status: str
    provenance_status: str


class MaisonRecommendationCard(BaseModel):
    fragrance: MaisonFragranceCard
    recommendation_type: str
    score: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    reason: str
    review_status: str
    relationship: str | None = None


class MaisonFragranceDetail(MaisonFragranceCard):
    concentration: str | None = None
    description: str | None = None
    notes: list[str] = Field(default_factory=list)
    scent_vector: MaisonScentVectorSummary | None = None
    recommendation_links: list[int] = Field(default_factory=list)
    inspired_by: list[MaisonRecommendationCard] = Field(default_factory=list)


class MaisonSimilarFragranceResult(MaisonRecommendationCard):
    rank: int = Field(ge=1)


class MaisonScentprintRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dimensions: dict[str, float]
    family: str | None = None
    mood: str | None = None
    occasion: str | None = None
    season: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class MaisonScentprintResult(BaseModel):
    rank: int = Field(ge=1)
    fragrance: MaisonFragranceCard
    score: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    review_status: str


class MaisonCatalogueExportRow(MaisonFragranceCard):
    concentration: str | None = None
    notes: list[str] = Field(default_factory=list)
    scent_vector: MaisonScentVectorSummary | None = None


class MaisonApiHealth(BaseModel):
    status: str
    service: str
    public_catalogue_records: int = Field(ge=0)
