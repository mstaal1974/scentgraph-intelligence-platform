from fastapi import APIRouter, HTTPException
from aromatwin.schemas.fragrance import FragranceRead, SimilarityMatch

router = APIRouter(tags=["catalogue"])


@router.get("/fragrances", response_model=list[FragranceRead])
def fragrances() -> list[FragranceRead]:
    return []


@router.get("/fragrances/{fragrance_id}", response_model=FragranceRead)
def fragrance(fragrance_id: int) -> FragranceRead:
    raise HTTPException(404, "Approved fragrance not found")


@router.get("/similar/{fragrance_id}", response_model=list[SimilarityMatch])
def similar(fragrance_id: int) -> list[SimilarityMatch]:
    return []
