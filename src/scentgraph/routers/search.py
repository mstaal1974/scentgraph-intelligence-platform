from fastapi import APIRouter, Query
from scentgraph.schemas.fragrance import SearchResult

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[SearchResult])
def search(q: str = Query(min_length=1)) -> list[SearchResult]:
    return []
