from fastapi import APIRouter

from scentgraph.schemas.recommendation import RecommendationRequest, RecommendationResponse
from scentgraph.services.recommendations import recommend

router = APIRouter(tags=["recommendations"])


@router.post("/recommend", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    return recommend(request)
