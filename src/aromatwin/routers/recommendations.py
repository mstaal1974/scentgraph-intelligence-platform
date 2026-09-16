from fastapi import APIRouter
from aromatwin.schemas.recommendation import RecommendationRequest, RecommendationResponse
from aromatwin.services.recommendations import recommend

router = APIRouter(tags=["intelligence"])


@router.post("/recommend", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    return recommend(request)
