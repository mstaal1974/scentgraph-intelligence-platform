"""Internal, authentication-ready review facade over existing guarded services."""

import csv
import io

from fastapi import APIRouter, HTTPException, Query, Response

from aromatwin.routers import enrichment_reviews, profile_drafts, recommendations, scent_vectors
from aromatwin.schemas.admin_review import (
    AdminBlockedItem,
    AdminReadinessReport,
    AdminReviewDecisionRequest,
    AdminReviewDecisionResult,
    AdminReviewQueueItem,
    AdminReviewSummary,
)
from aromatwin.services import admin_review
from aromatwin.services.enrichment_review import approve_enrichment_review, reject_enrichment_review
from aromatwin.services.profile_builder import approve_profile_draft, reject_profile_draft
from aromatwin.services.recommendation_engine import approve_recommendation, reject_recommendation
from aromatwin.services.scent_vector_engine import approve_scent_vector, reject_scent_vector

router = APIRouter(prefix="/admin", tags=["admin review"])
_DECISIONS: dict[tuple[str, str], dict[str, str | None]] = {}


def _queue() -> list[AdminReviewQueueItem]:
    queue = admin_review.build_review_queue()
    return [item.model_copy(update=_DECISIONS.get((item.stage, item.source_record_id), {}))
            for item in queue]


def _result(
    stage: str, record_id: str, status: str, reason: str, reviewer: str
) -> AdminReviewDecisionResult:
    return AdminReviewDecisionResult(
        accepted=True, stage=stage, record_id=record_id, status=status,
        reason=reason, reviewer=reviewer,
    )


@router.get("/health")
def admin_health() -> dict[str, str]:
    return {"status": "ok", "service": "admin-review"}


@router.get("/review/summary", response_model=AdminReviewSummary)
def summary() -> AdminReviewSummary:
    return admin_review.review_summary(_queue())


@router.get("/review/queue", response_model=list[AdminReviewQueueItem])
def queue(stage: str | None = Query(default=None)) -> list[AdminReviewQueueItem]:
    if stage is not None and stage not in admin_review.STAGES:
        raise HTTPException(404, "Unknown review stage")
    return [item for item in _queue() if stage is None or item.stage == stage]


@router.get("/review/queue/{stage}", response_model=list[AdminReviewQueueItem])
def stage_queue(stage: str) -> list[AdminReviewQueueItem]:
    if stage not in admin_review.STAGES:
        raise HTTPException(404, "Unknown review stage")
    return [item for item in _queue() if item.stage == stage]


@router.get("/review/blocked", response_model=list[AdminBlockedItem])
def blocked() -> list[AdminBlockedItem]:
    return admin_review.blocked_items(_queue())


@router.get("/review/readiness", response_model=AdminReadinessReport)
def readiness() -> AdminReadinessReport:
    return admin_review.readiness_report(_queue())


def _integer_id(record_id: str) -> int:
    try:
        return int(record_id)
    except ValueError as error:
        raise HTTPException(422, "This stage requires an integer record ID") from error


@router.post("/review/{stage}/{record_id}/approve", response_model=AdminReviewDecisionResult)
def approve(
    stage: str, record_id: str, decision: AdminReviewDecisionRequest
) -> AdminReviewDecisionResult:
    """Delegate approval to the existing service; never infer or force approval."""
    identifier = _integer_id(record_id)
    try:
        if stage == "profile_draft":
            current = profile_drafts._get(identifier)
            updated = approve_profile_draft(current)
            profile_drafts._DRAFTS[profile_drafts._DRAFTS.index(current)] = updated
        elif stage == "enrichment_review":
            current = enrichment_reviews._get(identifier)
            updated = approve_enrichment_review(
                current, enrichment_reviews._review_sources(current), decision.reviewer
            )
            enrichment_reviews._REVIEWS[enrichment_reviews._REVIEWS.index(current)] = updated
        elif stage == "scent_vector":
            current = scent_vectors._find(identifier)
            updated = approve_scent_vector(current)
            scent_vectors._VECTORS[scent_vectors._VECTORS.index(current)] = updated
        elif stage == "recommendation":
            current = recommendations._find(identifier)
            updated = approve_recommendation(current)
            recommendations._RECOMMENDATIONS[
                recommendations._RECOMMENDATIONS.index(current)
            ] = updated
        else:
            raise HTTPException(422, f"Approval is unsupported for stage '{stage}'")
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return _result(stage, record_id, updated.review_status, "Approved by guarded stage service",
                   decision.reviewer)


@router.post("/review/{stage}/{record_id}/reject", response_model=AdminReviewDecisionResult)
def reject(
    stage: str, record_id: str, decision: AdminReviewDecisionRequest
) -> AdminReviewDecisionResult:
    reason = (decision.reason or "").strip()
    if not reason:
        raise HTTPException(422, "A rejection reason is required")
    identifier = _integer_id(record_id)
    try:
        if stage == "profile_draft":
            current = profile_drafts._get(identifier)
            updated = reject_profile_draft(current, reason)
            profile_drafts._DRAFTS[profile_drafts._DRAFTS.index(current)] = updated
        elif stage == "enrichment_review":
            current = enrichment_reviews._get(identifier)
            updated = reject_enrichment_review(current, reason, decision.reviewer)
            enrichment_reviews._REVIEWS[enrichment_reviews._REVIEWS.index(current)] = updated
        elif stage == "scent_vector":
            current = scent_vectors._find(identifier)
            updated = reject_scent_vector(current, reason)
            scent_vectors._VECTORS[scent_vectors._VECTORS.index(current)] = updated
        elif stage == "recommendation":
            current = recommendations._find(identifier)
            updated = reject_recommendation(current, reason)
            recommendations._RECOMMENDATIONS[
                recommendations._RECOMMENDATIONS.index(current)
            ] = updated
        elif stage in admin_review.STAGES:
            # Stages without mutable foundation stores retain a console audit decision only.
            _DECISIONS[(stage, record_id)] = {
                "status": "rejected", "blocking_reason": reason,
                "reviewer": decision.reviewer, "next_action": "review_rejection",
            }
            return _result(stage, record_id, "rejected", reason, decision.reviewer)
        else:
            raise HTTPException(404, "Unknown review stage")
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return _result(stage, record_id, updated.review_status, reason, decision.reviewer)


@router.post(
    "/review/{stage}/{record_id}/request-more-sources",
    response_model=AdminReviewDecisionResult,
)
def request_more_sources(
    stage: str, record_id: str, decision: AdminReviewDecisionRequest
) -> AdminReviewDecisionResult:
    if stage not in {"profile_draft", "enrichment_review"}:
        raise HTTPException(422, f"Requesting more sources is unsupported for stage '{stage}'")
    reason = (decision.reason or "More independent sources are required").strip()
    _DECISIONS[(stage, record_id)] = {
        "status": "requires_more_sources", "blocking_reason": reason,
        "reviewer": decision.reviewer, "next_action": "request_more_sources",
    }
    return _result(stage, record_id, "requires_more_sources", reason, decision.reviewer)


@router.get("/export/review-queue")
def export_review_queue() -> Response:
    output = io.StringIO()
    fields = (
        "stage", "record_id", "title", "status", "confidence", "provenance_summary",
        "blocking_reason", "next_action",
    )
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(admin_review.export_rows(_queue()))
    return Response(
        output.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admin_review_queue.csv"},
    )
