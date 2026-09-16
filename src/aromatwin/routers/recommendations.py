from fastapi import APIRouter, HTTPException

from aromatwin.routers.catalogue import _CATALOGUE
from aromatwin.routers.scent_vectors import _VECTORS
from aromatwin.schemas.recommendation import (
    ContextualRecommendationRequest,
    RecommendationDecisionRequest,
    RecommendationGenerateRequest,
    RecommendationRead,
    RecommendationResult,
    SimilarFragranceRequest,
)
from aromatwin.services.recommendation_engine import (
    Recommendation,
    approve_recommendation,
    contextual_recommendations,
    generate_recommendations,
    public_recommendation,
    reject_recommendation,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
_RECOMMENDATIONS: list[Recommendation] = []


def _read(item: Recommendation) -> RecommendationRead:
    return RecommendationRead.model_validate(public_recommendation(item))


def _find(recommendation_id: int) -> Recommendation:
    item = next((value for value in _RECOMMENDATIONS if value.id == recommendation_id), None)
    if item is None:
        raise HTTPException(404, "Recommendation not found")
    return item


@router.get("", response_model=list[RecommendationRead])
def list_recommendations() -> list[RecommendationRead]:
    return [_read(item) for item in _RECOMMENDATIONS]


def _generate(source_id: int, limit: int) -> list[Recommendation]:
    source = next((item for item in _CATALOGUE if item.id == source_id), None)
    if source is None:
        raise HTTPException(422, "Only approved catalogue fragrances can be recommended")
    try:
        generated = generate_recommendations(
            source, _CATALOGUE, _VECTORS, _RECOMMENDATIONS, limit=limit
        )
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    for item in generated:
        if item not in _RECOMMENDATIONS:
            _RECOMMENDATIONS.append(item)
    return generated


@router.post("/generate", response_model=list[RecommendationRead], status_code=201)
def generate(request: RecommendationGenerateRequest) -> list[RecommendationRead]:
    return [_read(item) for item in _generate(request.source_fragrance_id, request.limit)]


@router.post("/similar-fragrances", response_model=list[RecommendationResult])
def similar_fragrances(request: SimilarFragranceRequest) -> list[RecommendationResult]:
    generated = _generate(request.source_fragrance_id, request.limit)
    return [
        RecommendationResult(
            fragrance_id=item.recommended_fragrance_id,
            score=item.score,
            reason=item.reason,
            recommendation=_read(item),
        )
        for item in generated
        if item.score >= request.minimum_score
    ]


@router.post("/contextual", response_model=list[RecommendationResult])
def contextual(request: ContextualRecommendationRequest) -> list[RecommendationResult]:
    try:
        results = contextual_recommendations(_CATALOGUE, _VECTORS, **request.model_dump())
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return [RecommendationResult.model_validate(item) for item in results]


@router.get("/{recommendation_id}", response_model=RecommendationRead)
def get_recommendation(recommendation_id: int) -> RecommendationRead:
    return _read(_find(recommendation_id))


@router.post("/{recommendation_id}/approve", response_model=RecommendationRead)
def approve(recommendation_id: int) -> RecommendationRead:
    current = _find(recommendation_id)
    try:
        updated = approve_recommendation(current)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    _RECOMMENDATIONS[_RECOMMENDATIONS.index(current)] = updated
    return _read(updated)


@router.post("/{recommendation_id}/reject", response_model=RecommendationRead)
def reject(recommendation_id: int, request: RecommendationDecisionRequest) -> RecommendationRead:
    current = _find(recommendation_id)
    try:
        updated = reject_recommendation(current, request.reason or "")
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    _RECOMMENDATIONS[_RECOMMENDATIONS.index(current)] = updated
    return _read(updated)
