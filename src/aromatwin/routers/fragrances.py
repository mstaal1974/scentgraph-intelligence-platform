from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.fragrance import FragranceRead, SimilarityMatch
from aromatwin.security import require_private_api_key

router = APIRouter(tags=["catalogue"], dependencies=[Depends(require_private_api_key)])


@router.get("/fragrances", response_model=list[FragranceRead])
def fragrances() -> list[FragranceRead]:
    return []


@router.get("/fragrances/{fragrance_id}", response_model=FragranceRead)
def fragrance(fragrance_id: int) -> FragranceRead:
    raise HTTPException(404, "Approved fragrance not found")


@router.get("/similar/{fragrance_id}", response_model=list[SimilarityMatch])
def similar(fragrance_id: int) -> list[SimilarityMatch]:
    return []
