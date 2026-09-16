from fastapi import APIRouter, HTTPException

from scentgraph.schemas.fragrance import FragranceRead, SimilarityMatch

router = APIRouter(tags=["fragrances"])
_SAMPLE = [
    FragranceRead(
        id=1,
        brand_id=1,
        name="Lost Cherry",
        slug="lost-cherry",
        concentration="eau de parfum",
        family="amber floral",
        source_confidence=0.5,
    )
]


@router.get("/fragrances", response_model=list[FragranceRead])
def list_fragrances() -> list[FragranceRead]:
    return _SAMPLE


@router.get("/fragrances/{fragrance_id}", response_model=FragranceRead)
def get_fragrance(fragrance_id: int) -> FragranceRead:
    match = next((item for item in _SAMPLE if item.id == fragrance_id), None)
    if not match:
        raise HTTPException(404, "Fragrance not found")
    return match


@router.get("/similar/{fragrance_id}", response_model=list[SimilarityMatch])
def similar(fragrance_id: int) -> list[SimilarityMatch]:
    return []
