from fastapi import APIRouter, Depends

from aromatwin.schemas.scentprint import ScentprintRequest, ScentprintResponse
from aromatwin.security import require_private_api_key
from aromatwin.services.scentprint import match_scentprint

router = APIRouter(tags=["intelligence"], dependencies=[Depends(require_private_api_key)])


@router.post("/scentprint", response_model=ScentprintResponse)
def scentprint(request: ScentprintRequest) -> ScentprintResponse:
    return match_scentprint(request)
