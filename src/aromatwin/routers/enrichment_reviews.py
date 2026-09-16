from fastapi import APIRouter, HTTPException
from aromatwin.schemas.enrichment_review import EnrichmentReviewRead, ReviewDecisionRequest

router = APIRouter(prefix="/enrichment-reviews", tags=["independent enrichment"])
_REVIEWS: list[EnrichmentReviewRead] = []


def _get(review_id: int) -> EnrichmentReviewRead:
    review = next((item for item in _REVIEWS if item.id == review_id), None)
    if review is None:
        raise HTTPException(404, "Enrichment review not found")
    return review


@router.get("", response_model=list[EnrichmentReviewRead])
def list_reviews() -> list[EnrichmentReviewRead]:
    return _REVIEWS


@router.get("/{review_id}", response_model=EnrichmentReviewRead)
def get_review(review_id: int) -> EnrichmentReviewRead:
    return _get(review_id)


@router.post("/{review_id}/approve", response_model=EnrichmentReviewRead)
def approve_review(review_id: int, decision: ReviewDecisionRequest) -> EnrichmentReviewRead:
    return _get(review_id)


@router.post("/{review_id}/reject", response_model=EnrichmentReviewRead)
def reject_review(review_id: int, decision: ReviewDecisionRequest) -> EnrichmentReviewRead:
    return _get(review_id)
