from fastapi import APIRouter, Depends

from aromatwin.schemas.brand import BrandRead
from aromatwin.security import require_private_api_key

router = APIRouter(
    prefix="/brands", tags=["catalogue"], dependencies=[Depends(require_private_api_key)]
)


@router.get("", response_model=list[BrandRead])
def brands() -> list[BrandRead]:
    return []
