from fastapi import APIRouter
from scentgraph.schemas.scentprint import ScentprintRequest, ScentprintResponse
from scentgraph.services.scentprint import match_scentprint

router = APIRouter(tags=["scentprint"])


@router.post("/scentprint", response_model=ScentprintResponse)
def scentprint(request: ScentprintRequest) -> ScentprintResponse:
    return match_scentprint(request)
