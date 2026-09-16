"""Aggregate allowlisted workflow metadata for human review.

The module intentionally reads only known public-safe columns.  Unknown CSV fields are never
copied into queue records, which makes supplier commercial data and third-party content
unrepresentable in the admin API contract.
"""

import csv
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from aromatwin.schemas.admin_review import (
    AdminBlockedItem,
    AdminReadinessReport,
    AdminReviewQueueItem,
    AdminReviewStageSummary,
    AdminReviewSummary,
)

STAGES = (
    "supplier_import",
    "match_candidate",
    "profile_draft",
    "enrichment_review",
    "catalogue_promotion",
    "scent_vector",
    "recommendation",
    "maison_api_ready",
)
DATA_FILES = {
    "profile_draft": "profile_drafts.csv",
    "enrichment_review": "enrichment_reviews.csv",
    "catalogue_promotion": "catalogue_fragrances.csv",
    "scent_vector": "scent_vectors.csv",
    "recommendation": "recommendations.csv",
}
READY_STATUSES = {"ready_for_approval", "approved_for_catalogue", "approved", "published"}
HUMAN_STATUSES = {"needs_human_review", "needs_review", "needs_verification", "match_candidate"}
REJECTED_STATUSES = {"rejected", "rejected_low_confidence", "rejected_licensing_risk"}


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _score(row: dict[str, str]) -> float:
    for key in ("confidence_score", "source_confidence", "match_confidence", "score"):
        try:
            value = float(row.get(key) or "")
            return max(0.0, min(1.0, value))
        except ValueError:
            pass
    return 0.0


def _title(stage: str, row: dict[str, str]) -> str:
    brand = (row.get("brand") or row.get("candidate_brand") or "").strip()
    name = (row.get("fragrance_name") or row.get("name") or "").strip()
    if brand or name:
        return " ".join(value for value in (brand, name) if value)
    if stage == "recommendation":
        return f"Recommendation {row.get('source_fragrance_id', '?')} → " \
            f"{row.get('recommended_fragrance_id', '?')}"
    return f"{stage.replace('_', ' ').title()} {row.get('id', '')}".strip()


def _provenance(stage: str, row: dict[str, str]) -> str:
    explicit = (row.get("provenance_summary") or row.get("provenance_notes") or "").strip()
    if explicit:
        return explicit
    references = (row.get("provenance_references") or "").strip()
    if references:
        return "Recorded provenance references are available for human verification."
    if stage == "recommendation" and (row.get("generation_method") or "").strip():
        return "Generated from approved public-safe catalogue and vector metadata."
    return "No provenance summary recorded."


def _blocking_reason(stage: str, row: dict[str, str], provenance: str, score: float) -> str | None:
    status = (row.get("review_status") or row.get("status") or "needs_human_review").lower()
    reason = (row.get("rejection_reason") or "").strip()
    if reason:
        return reason
    if _truthy(row.get("copied_restricted_content")):
        return "Copied restricted content detected"
    if (row.get("licensing_risk") or "").strip().lower() == "high":
        return "High licensing risk"
    if provenance.startswith("No provenance"):
        return "Missing provenance"
    if status in REJECTED_STATUSES:
        return "Rejected without a recorded reason"
    if score < 0.75 and stage not in {"supplier_import", "catalogue_promotion"}:
        return "Low confidence requires additional verification"
    return None


def _next_action(status: str, blocked: str | None) -> str:
    if blocked:
        if "provenance" in blocked.lower() or "confidence" in blocked.lower():
            return "request_more_sources"
        return "resolve_blocker"
    if status in READY_STATUSES:
        return "approve" if status == "ready_for_approval" else "monitor_next_stage"
    if status in REJECTED_STATUSES:
        return "review_rejection"
    return "human_review"


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_review_queue(data_dir: Path | str = Path("data")) -> list[AdminReviewQueueItem]:
    root = Path(data_dir)
    items: list[AdminReviewQueueItem] = []
    for stage, filename in DATA_FILES.items():
        for offset, row in enumerate(_read(root / filename), 1):
            record_id = str(row.get("id") or offset)
            status = (row.get("review_status") or row.get("status") or
                      ("approved" if stage == "catalogue_promotion" else "needs_human_review"))
            score = _score(row)
            provenance = _provenance(stage, row)
            blocker = _blocking_reason(stage, row, provenance, score)
            updated = row.get("updated_at") or None
            items.append(AdminReviewQueueItem(
                id=f"{stage}:{record_id}", stage=stage, source_record_id=record_id,
                title=_title(stage, row), status=status, confidence_score=score,
                source_confidence=score,
                licensing_risk=(row.get("licensing_risk") or "unknown").lower(),
                copied_restricted_content_detected=_truthy(
                    row.get("copied_restricted_content")
                ),
                provenance_summary=provenance, blocking_reason=blocker,
                reviewer=(row.get("reviewer") or "").strip() or None,
                updated_at=updated, next_action=_next_action(status, blocker),
            ))
    # Catalogue items with approved vectors and recommendations represent API readiness.
    catalogue = [item for item in items if item.stage == "catalogue_promotion"]
    vectors = [item for item in items if item.stage == "scent_vector"]
    recommendations = [item for item in items if item.stage == "recommendation"]
    for record in catalogue:
        ready = bool(vectors and recommendations) and all(
            not item.blocking_reason for item in (*vectors, *recommendations)
        )
        status = "ready_for_approval" if ready else "not_ready"
        blocker = None if ready else "Approved vector and recommendation evidence is required"
        items.append(record.model_copy(update={
            "id": f"maison_api_ready:{record.source_record_id}",
            "stage": "maison_api_ready", "status": status, "blocking_reason": blocker,
            "next_action": _next_action(status, blocker),
        }))
    return items


def review_summary(items: Iterable[AdminReviewQueueItem]) -> AdminReviewSummary:
    queue = list(items)
    stages = []
    for stage in STAGES:
        records = [item for item in queue if item.stage == stage]
        statuses = Counter(item.status for item in records)
        stages.append(AdminReviewStageSummary(
            stage=stage, total=len(records), by_status=dict(statuses),
            blocked=sum(bool(item.blocking_reason) for item in records),
            requiring_human_review=sum(item.status in HUMAN_STATUSES for item in records),
            ready_for_approval=sum(item.status == "ready_for_approval" for item in records),
        ))
    return AdminReviewSummary(
        total=len(queue), by_status=dict(Counter(item.status for item in queue)), stages=stages,
        blocked=sum(bool(item.blocking_reason) for item in queue),
        requiring_human_review=sum(item.status in HUMAN_STATUSES for item in queue),
        ready_for_approval=sum(item.status == "ready_for_approval" for item in queue),
    )


def blocked_items(items: Iterable[AdminReviewQueueItem]) -> list[AdminBlockedItem]:
    return [AdminBlockedItem(
        id=item.id, stage=item.stage, source_record_id=item.source_record_id,
        title=item.title, status=item.status, blocking_reason=item.blocking_reason or "",
        next_action=item.next_action,
    ) for item in items if item.blocking_reason]


def readiness_report(items: Iterable[AdminReviewQueueItem]) -> AdminReadinessReport:
    queue = list(items)
    ready = [item for item in queue if item.status in READY_STATUSES and not item.blocking_reason]
    not_ready = blocked_items(queue)
    return AdminReadinessReport(
        ready=ready, not_ready=not_ready, ready_count=len(ready),
        not_ready_count=len(not_ready),
        maison_api_ready_count=sum(
            item.stage == "maison_api_ready" and item.status == "ready_for_approval"
            for item in queue
        ),
    )


def export_rows(items: Iterable[AdminReviewQueueItem]) -> list[dict[str, object]]:
    """Return a strict export allowlist; never pass through source row dictionaries."""
    return [{
        "stage": item.stage, "record_id": item.source_record_id, "title": item.title,
        "status": item.status, "confidence": item.confidence_score,
        "provenance_summary": item.provenance_summary,
        "blocking_reason": item.blocking_reason or "", "next_action": item.next_action,
    } for item in items]


def decision_timestamp() -> datetime:
    return datetime.now(UTC)
