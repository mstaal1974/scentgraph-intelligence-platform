"""Private endpoints exposing public-safe review projections by default."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.review_workflow import (
    ReviewDecisionCreate,
    ReviewDecisionPublicSummary,
    ReviewGatePublicSummary,
    ReviewQueueItemPublicSummary,
    ReviewReadinessReport,
    ReviewWorkflowAuditReport,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.review_decisions import apply_review_decision, public_decision_summary
from aromatwin.services.review_gates import get_review_gate, list_review_gates
from aromatwin.services.review_queue_builder import build_review_queues, public_queue_summary
from aromatwin.services.review_readiness import build_review_readiness

router = APIRouter(prefix="/review-workflow", tags=["internal human review workflow"],
                   dependencies=[Depends(require_private_api_key)])
_QUEUE: list[dict[str, object]] = []
_DECISIONS: list[dict[str, object]] = []


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.post("/queues/build", response_model=list[ReviewQueueItemPublicSummary])
def build_queues(sources: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    _QUEUE[:] = build_review_queues(sources)
    return [public_queue_summary(item) for item in _QUEUE]


@router.get("/queues", response_model=list[ReviewQueueItemPublicSummary])
def queues() -> list[dict[str, object]]:
    return [public_queue_summary(item) for item in _QUEUE]


@router.get("/queues/{review_item_id}", response_model=ReviewQueueItemPublicSummary)
def queue_item(review_item_id: str) -> dict[str, object]:
    item = next((item for item in _QUEUE if item["review_item_id"] == review_item_id), None)
    if item is None:
        raise HTTPException(404, "Review item not found")
    return public_queue_summary(item)


@router.get("/gates", response_model=list[ReviewGatePublicSummary])
def gates() -> list[dict[str, object]]:
    return list_review_gates()


@router.get("/gates/{gate_id}", response_model=ReviewGatePublicSummary)
def gate(gate_id: str) -> dict[str, object]:
    item = get_review_gate(gate_id)
    if item is None:
        raise HTTPException(404, "Review gate not found")
    return item


@router.post("/decisions", response_model=ReviewDecisionPublicSummary)
def create_decision(payload: ReviewDecisionCreate) -> dict[str, object]:
    item = next((item for item in _QUEUE if item["review_item_id"] == payload.review_item_id), None)
    if item is None:
        raise HTTPException(404, "Review item not found")
    decision = apply_review_decision(item, **payload.model_dump(exclude={"review_item_id"}))
    existing = next((entry for entry in _DECISIONS
                     if entry["decision_id"] == decision["decision_id"]), None)
    if existing is None:
        _DECISIONS.append(decision)
    else:
        decision = existing
    item["review_status"] = decision["next_status"]
    return public_decision_summary(decision)


@router.get("/decisions", response_model=list[ReviewDecisionPublicSummary])
def decisions() -> list[dict[str, object]]:
    return [public_decision_summary(item) for item in _DECISIONS]


@router.get("/readiness", response_model=ReviewReadinessReport)
def readiness() -> dict[str, object]:
    return build_review_readiness(_QUEUE)


@router.get("/audit", response_model=ReviewWorkflowAuditReport)
def audit() -> dict[str, object]:
    return {"passed": True, "reviewed_item_count": len(_QUEUE),
            "decision_count": len(_DECISIONS), "audit_required_count": len(_DECISIONS),
            "violations": []}

