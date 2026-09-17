from fastapi import APIRouter, Depends, Query

from aromatwin.schemas.fragrance import SearchResult
from aromatwin.security import require_private_api_key

router = APIRouter(tags=["catalogue"], dependencies=[Depends(require_private_api_key)])


@router.get("/search", response_model=list[SearchResult])
def search(q: str = Query(min_length=1)) -> list[SearchResult]:
    return []
