from scentgraph.schemas.recommendation import RecommendationRequest, RecommendationResponse


def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """Foundation boundary; ranking strategies will plug in without changing transport code."""
    return RecommendationResponse(
        strategy=request.strategy, status="foundation_placeholder", recommendations=[]
    )
