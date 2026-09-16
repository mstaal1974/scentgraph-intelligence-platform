from fastapi import APIRouter, HTTPException

from scentgraph.schemas.brand import BrandRead

router = APIRouter(prefix="/brands", tags=["brands"])
_SAMPLE = [
    BrandRead(id=1, name="Tom Ford", slug="tom-ford", country="United States", verified=False)
]


@router.get("", response_model=list[BrandRead])
def list_brands() -> list[BrandRead]:
    return _SAMPLE


@router.get("/{brand_id}", response_model=BrandRead)
def get_brand(brand_id: int) -> BrandRead:
    match = next((item for item in _SAMPLE if item.id == brand_id), None)
    if not match:
        raise HTTPException(404, "Brand not found")
    return match
