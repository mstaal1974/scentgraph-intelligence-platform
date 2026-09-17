from fastapi import APIRouter, Depends, HTTPException

from aromatwin.routers.enrichment_reviews import _REVIEWS
from aromatwin.schemas.catalogue import (
    CatalogueBrandRead,
    CatalogueFragranceRead,
    CataloguePromotionDecision,
    CataloguePromotionRequest,
    CataloguePromotionResult,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.catalogue_promotion import CatalogueFragrance, promote_enrichment_review

router = APIRouter(
    prefix="/catalogue",
    tags=["catalogue promotion"],
    dependencies=[Depends(require_private_api_key)],
)
_CATALOGUE: list[CatalogueFragrance] = []


@router.get("/fragrances", response_model=list[CatalogueFragranceRead])
def list_catalogue_fragrances() -> list[CatalogueFragrance]:
    return _CATALOGUE


@router.get("/fragrances/{fragrance_id}", response_model=CatalogueFragranceRead)
def get_catalogue_fragrance(fragrance_id: int) -> CatalogueFragrance:
    record = next((item for item in _CATALOGUE if item.id == fragrance_id), None)
    if record is None:
        raise HTTPException(404, "Catalogue fragrance not found")
    return record


@router.post("/promote", response_model=CataloguePromotionResult, status_code=201)
def promote_catalogue(request: CataloguePromotionRequest) -> CataloguePromotionResult:
    review = next((item for item in _REVIEWS if item.id == request.enrichment_review_id), None)
    if review is None:
        raise HTTPException(404, "Enrichment review not found")
    try:
        fragrance = promote_enrichment_review(review, _CATALOGUE)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if fragrance not in _CATALOGUE:
        _CATALOGUE.append(fragrance)
    return CataloguePromotionResult(
        decision=CataloguePromotionDecision(accepted=True, reason="promoted"),
        fragrance=CatalogueFragranceRead.model_validate(fragrance),
    )


@router.get("/brands", response_model=list[CatalogueBrandRead])
def list_catalogue_brands() -> list[CatalogueBrandRead]:
    unique = {item.brand_id: item for item in _CATALOGUE}
    return [
        CatalogueBrandRead(id=item.brand_id, name=item.brand, slug=item.brand_slug)
        for item in unique.values()
    ]


@router.get("/brands/{brand_id}", response_model=CatalogueBrandRead)
def get_catalogue_brand(brand_id: int) -> CatalogueBrandRead:
    item = next((record for record in _CATALOGUE if record.brand_id == brand_id), None)
    if item is None:
        raise HTTPException(404, "Catalogue brand not found")
    return CatalogueBrandRead(id=item.brand_id, name=item.brand, slug=item.brand_slug)
