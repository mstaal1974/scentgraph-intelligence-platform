from types import SimpleNamespace

from fastapi import APIRouter, HTTPException

from aromatwin.schemas.enrichment_review import (
    EnrichmentReviewDecisionRequest,
    EnrichmentReviewGenerateRequest,
    EnrichmentReviewRead,
    EnrichmentSourceCreate,
    EnrichmentSourceRead,
)
from aromatwin.services.enrichment_review import (
    EnrichmentReview,
    EnrichmentSource,
    approve_enrichment_review,
    build_enrichment_review,
    mark_enrichment_ready,
    reject_enrichment_review,
)

router = APIRouter(tags=["independent enrichment"])
_REVIEWS: list[EnrichmentReview] = []
_SOURCES: list[EnrichmentSource] = []


def _get(review_id: int) -> EnrichmentReview:
    review = next((item for item in _REVIEWS if item.id == review_id), None)
    if review is None:
        raise HTTPException(404, "Enrichment review not found")
    return review


def _review_sources(review: EnrichmentReview) -> list[EnrichmentSource]:
    return [source for source in _SOURCES if source.id in review.source_ids]


@router.get("/enrichment-reviews", response_model=list[EnrichmentReviewRead])
def list_reviews() -> list[EnrichmentReview]:
    return _REVIEWS


@router.get("/enrichment-reviews/{enrichment_review_id}", response_model=EnrichmentReviewRead)
def get_review(enrichment_review_id: int) -> EnrichmentReview:
    return _get(enrichment_review_id)


@router.post("/enrichment-reviews/generate", response_model=EnrichmentReviewRead, status_code=201)
def generate_enrichment_review(request: EnrichmentReviewGenerateRequest) -> EnrichmentReview:
    source_ids = set(request.source_ids)
    sources = [source for source in _SOURCES if source.id in source_ids]
    if len(sources) != len(source_ids):
        raise HTTPException(422, "One or more enrichment sources do not exist")
    draft = SimpleNamespace(
        id=request.profile_draft_id,
        brand=request.brand,
        fragrance_name=request.fragrance_name,
        concentration=request.concentration,
        review_status=request.profile_draft_status,
    )
    try:
        review = build_enrichment_review(draft, sources, enrichment_review_id=len(_REVIEWS) + 1)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    _REVIEWS.append(review)
    return review


def _replace(review: EnrichmentReview, updated: EnrichmentReview) -> EnrichmentReview:
    _REVIEWS[_REVIEWS.index(review)] = updated
    return updated


@router.post(
    "/enrichment-reviews/{enrichment_review_id}/mark-ready",
    response_model=EnrichmentReviewRead,
)
def mark_ready(enrichment_review_id: int) -> EnrichmentReview:
    review = _get(enrichment_review_id)
    try:
        return _replace(review, mark_enrichment_ready(review, _review_sources(review)))
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.post(
    "/enrichment-reviews/{enrichment_review_id}/approve", response_model=EnrichmentReviewRead
)
def approve_review(
    enrichment_review_id: int, decision: EnrichmentReviewDecisionRequest
) -> EnrichmentReview:
    review = _get(enrichment_review_id)
    try:
        approved = approve_enrichment_review(review, _review_sources(review), decision.reviewer)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return _replace(review, approved)


@router.post(
    "/enrichment-reviews/{enrichment_review_id}/reject", response_model=EnrichmentReviewRead
)
def reject_review(
    enrichment_review_id: int, decision: EnrichmentReviewDecisionRequest
) -> EnrichmentReview:
    review = _get(enrichment_review_id)
    try:
        rejected = reject_enrichment_review(review, decision.reason or "", decision.reviewer)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return _replace(review, rejected)


@router.get("/enrichment-sources", response_model=list[EnrichmentSourceRead])
def list_sources() -> list[EnrichmentSource]:
    return _SOURCES


@router.post("/enrichment-sources", response_model=EnrichmentSourceRead, status_code=201)
def create_source(request: EnrichmentSourceCreate) -> EnrichmentSource:
    source = EnrichmentSource(id=len(_SOURCES) + 1, **request.model_dump(mode="json"))
    _SOURCES.append(source)
    return source
