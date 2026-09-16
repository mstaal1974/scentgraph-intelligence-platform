from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from aromatwin.database import get_db
from aromatwin.repositories.enrichment import EnrichmentRepository
from aromatwin.schemas.enrichment import (
    EnrichmentDecisionRequest,
    EnrichmentGenerateRequest,
    EnrichmentReviewRead,
    EnrichmentSourceCreate,
    EnrichmentSourceRead,
    ProfileSourceLinkCreate,
    ProfileSourceLinkRead,
)
from aromatwin.services.enrichment import (
    EnrichmentEventData,
    approve_enrichment_review,
    generate_enrichment_review,
    mark_ready,
    reject_enrichment,
)

router = APIRouter(tags=["enrichment review"])


def get_enrichment_repository(db: Session = Depends(get_db)) -> EnrichmentRepository:
    return EnrichmentRepository(db)


@router.get("/enrichment-sources", response_model=list[EnrichmentSourceRead])
def list_sources(
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> list[object]:
    return repository.list_sources()


@router.post("/enrichment-sources", response_model=EnrichmentSourceRead, status_code=201)
def create_source(
    payload: EnrichmentSourceCreate,
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> object:
    try:
        return repository.add_source(payload)
    except IntegrityError as error:
        raise HTTPException(409, "Source violates permission constraints") from error


@router.get("/enrichment-reviews", response_model=list[EnrichmentReviewRead])
def list_reviews(
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> list[object]:
    return repository.list_reviews()


@router.get("/enrichment-reviews/{review_id}", response_model=EnrichmentReviewRead)
def get_review(
    review_id: int, repository: EnrichmentRepository = Depends(get_enrichment_repository)
) -> object:
    review = repository.get_review(review_id)
    if review is None:
        raise HTTPException(404, "Enrichment review not found")
    return review


@router.post(
    "/enrichment-reviews/generate", response_model=list[EnrichmentReviewRead], status_code=201
)
def generate_reviews(
    payload: EnrichmentGenerateRequest,
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> list[object]:
    reviews = []
    events = []
    for profile in repository.profiles_for_generation(payload):
        generated = generate_enrichment_review(profile, repository.linked_sources(profile.id))
        review = repository.add_review(generated)
        reviews.append(review)
        events.append(
            EnrichmentEventData(
                profile.id,
                "enrichment_generated",
                "Deterministic original enrichment generated; human review required.",
                "system",
            )
        )
    return repository.commit_generated(reviews, events)


def _review_or_404(review_id: int, repository: EnrichmentRepository) -> object:
    review = repository.get_review(review_id)
    if review is None:
        raise HTTPException(404, "Enrichment review not found")
    return review


@router.post(
    "/enrichment-reviews/{review_id}/attach-source",
    response_model=ProfileSourceLinkRead,
    status_code=201,
)
def attach_source(
    review_id: int,
    payload: ProfileSourceLinkCreate,
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> object:
    review = _review_or_404(review_id, repository)
    try:
        return repository.attach_source(review, payload, "reviewer")
    except ValueError as error:
        raise HTTPException(404, str(error)) from error
    except IntegrityError as error:
        raise HTTPException(409, "Source is already linked for this usage") from error


@router.post("/enrichment-reviews/{review_id}/mark-ready", response_model=EnrichmentReviewRead)
def ready(
    review_id: int,
    decision: EnrichmentDecisionRequest,
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> object:
    review = _review_or_404(review_id, repository)
    try:
        _, event = mark_ready(
            review, repository.linked_sources(review.profile_draft_id), decision.reviewer
        )
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    return repository.save_with_event(review, event)


@router.post("/enrichment-reviews/{review_id}/approve", response_model=EnrichmentReviewRead)
def approve(
    review_id: int,
    decision: EnrichmentDecisionRequest,
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> object:
    review = _review_or_404(review_id, repository)
    try:
        _, event = approve_enrichment_review(
            review, repository.linked_sources(review.profile_draft_id), decision
        )
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    return repository.save_with_event(review, event)


@router.post("/enrichment-reviews/{review_id}/reject", response_model=EnrichmentReviewRead)
def reject(
    review_id: int,
    decision: EnrichmentDecisionRequest,
    repository: EnrichmentRepository = Depends(get_enrichment_repository),
) -> object:
    review = _review_or_404(review_id, repository)
    try:
        _, event = reject_enrichment(review, decision)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return repository.save_with_event(review, event)
