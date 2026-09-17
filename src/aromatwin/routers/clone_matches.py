from fastapi import APIRouter, Depends

from aromatwin.schemas.fragrance import CloneMatch
from aromatwin.security import require_private_api_key

router = APIRouter(tags=["clone intelligence"], dependencies=[Depends(require_private_api_key)])


@router.get("/clone-matches/{fragrance_id}", response_model=list[CloneMatch])
def clone_matches(fragrance_id: int) -> list[CloneMatch]:
    return []
