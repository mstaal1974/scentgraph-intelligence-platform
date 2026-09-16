from fastapi import APIRouter

from scentgraph.schemas.fragrance import CloneMatch

router = APIRouter(tags=["clone intelligence"])


@router.get("/clone-matches/{fragrance_id}", response_model=list[CloneMatch])
def clone_matches(fragrance_id: int) -> list[CloneMatch]:
    return []
