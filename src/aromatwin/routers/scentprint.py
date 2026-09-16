from fastapi import APIRouter
from aromatwin.schemas.scentprint import ScentprintRequest, ScentprintResponse
from aromatwin.services.scentprint import match_scentprint

router = APIRouter(tags=["intelligence"])


@router.post("/scentprint", response_model=ScentprintResponse)
def scentprint(request: ScentprintRequest) -> ScentprintResponse:
    return match_scentprint(request)
