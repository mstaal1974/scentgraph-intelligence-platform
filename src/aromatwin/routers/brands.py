from fastapi import APIRouter
from aromatwin.schemas.brand import BrandRead

router = APIRouter(prefix="/brands", tags=["catalogue"])


@router.get("", response_model=list[BrandRead])
def brands() -> list[BrandRead]:
    return []
