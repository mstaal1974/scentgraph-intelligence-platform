from aromatwin.schemas.recommendation import RecommendationRequest, RecommendationResponse


def recommend(request: RecommendationRequest) -> RecommendationResponse:
    return RecommendationResponse(
        strategy=request.strategy, status="foundation_placeholder", recommendations=[]
    )
