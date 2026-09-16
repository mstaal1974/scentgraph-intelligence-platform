"""Public-safe Maison Obsidian integration endpoints."""

from fastapi import APIRouter, HTTPException

from aromatwin.schemas.maison import (
    MaisonApiHealth,
    MaisonCatalogueExportRow,
    MaisonFragranceCard,
    MaisonFragranceDetail,
    MaisonRecommendationCard,
    MaisonScentprintRequest,
    MaisonScentprintResult,
    MaisonSimilarFragranceResult,
)
from aromatwin.services.maison_integration import MaisonIntegrationService

router = APIRouter(prefix="/maison", tags=["maison"])
SERVICE = MaisonIntegrationService()


@router.get("/health", response_model=MaisonApiHealth)
def health() -> MaisonApiHealth:
    return MaisonApiHealth(
        status="ok", service="maison-integration", public_catalogue_records=len(SERVICE.catalogue)
    )


@router.get("/fragrances", response_model=list[MaisonFragranceCard])
def fragrances() -> list[MaisonFragranceCard]:
    return SERVICE.list_fragrances()


@router.get("/fragrances/slug/{slug}", response_model=MaisonFragranceDetail)
def fragrance_by_slug(slug: str) -> MaisonFragranceDetail:
    result = SERVICE.by_slug(slug)
    if result is None:
        raise HTTPException(404, "Public fragrance not found")
    return result


@router.get("/fragrances/{fragrance_id}/similar", response_model=list[MaisonSimilarFragranceResult])
def similar(fragrance_id: int) -> list[MaisonSimilarFragranceResult]:
    result = SERVICE.similar(fragrance_id)
    if result is None:
        raise HTTPException(404, "Public fragrance not found")
    return result


@router.get(
    "/fragrances/{fragrance_id}/recommendations", response_model=list[MaisonRecommendationCard]
)
def recommendations(fragrance_id: int) -> list[MaisonRecommendationCard]:
    result = SERVICE.recommendations_for(fragrance_id)
    if result is None:
        raise HTTPException(404, "Public fragrance not found")
    return result


@router.get("/fragrances/{fragrance_id}", response_model=MaisonFragranceDetail)
def fragrance(fragrance_id: int) -> MaisonFragranceDetail:
    result = SERVICE.detail(fragrance_id)
    if result is None:
        raise HTTPException(404, "Public fragrance not found")
    return result


@router.post("/scentprint/match", response_model=list[MaisonScentprintResult])
def scentprint_match(request: MaisonScentprintRequest) -> list[MaisonScentprintResult]:
    try:
        return SERVICE.scentprint(request)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.get("/export/catalogue", response_model=list[MaisonCatalogueExportRow])
def export_catalogue() -> list[MaisonCatalogueExportRow]:
    return SERVICE.catalogue_export()


@router.get("/export/recommendations", response_model=list[MaisonRecommendationCard])
def export_recommendations() -> list[MaisonRecommendationCard]:
    return SERVICE.recommendation_export()
