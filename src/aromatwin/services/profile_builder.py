from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any
from dataclasses import dataclass
from aromatwin.schemas.profile_draft import (
    ProfileDraftCreate,
    ProfileDraftDecisionRequest,
    ProfileDraftRead,
    ProfileDraftStatus,
)

RESTRICTED_INPUT_FIELDS = frozenset(
    {
        "description",
        "reviews",
        "review",
        "comments",
        "images",
        "image",
        "ratings",
        "rating",
        "user_generated_content",
        "ugc",
        "aed_price",
        "usd_price",
        "price",
        "cost",
        "supplier_cn_code",
        "supplier_code",
        "commercial_terms",
    }
)
APPROVABLE_SOURCE_TYPES = frozenset({"official_source", "licensed_commercial"})
APPROVABLE_LICENCE_STATUSES = frozenset(
    {"official_source", "licensed_commercial", "permission_documented"}
)
MINIMUM_APPROVAL_CONFIDENCE = 0.7


@dataclass(frozen=True)
class ApprovalEvidence:
    source_name: str
    source_type: str
    source_reference: str | None
    source_url: str | None
    licence_status: str
    commercial_use_allowed: bool
    confidence: float


def _safe_text(record: Mapping[str, Any], key: str, fallback: str = "") -> str:
    value = record.get(key, fallback)
    return str(value).strip() if value is not None else fallback


def generate_profile_draft(
    supplier: Mapping[str, Any], candidate: Mapping[str, Any]
) -> ProfileDraftCreate:
    """Build original deterministic draft text from identifiers, never third-party content."""
    supplier_id = int(supplier["id"])
    candidate_id = int(candidate["id"]) if candidate.get("id") not in (None, "") else None
    brand = (
        _safe_text(candidate, "candidate_brand")
        or _safe_text(supplier, "normalised_brand")
        or _safe_text(supplier, "supplier_brand_raw")
    )
    name = (
        _safe_text(candidate, "candidate_fragrance_name")
        or _safe_text(supplier, "normalised_name")
        or _safe_text(supplier, "supplier_name_raw")
    )
    source_type = _safe_text(candidate, "candidate_source_type", "unknown").casefold()
    match_confidence = float(candidate.get("match_confidence") or 0)
    is_restricted = source_type in {"reference_only", "restricted_non_commercial", "unknown"}
    source_confidence = min(match_confidence, 0.35) if is_restricted else min(match_confidence, 0.8)
    confidence = round(source_confidence * 0.8, 3)
    provenance = (
        f"Supplier item {supplier_id}; match candidate {candidate_id or 'unpersisted'}; source type {source_type}. "
        + (
            "Reference-only identifiers were used for discovery; independent permitted sources are required."
            if is_restricted
            else "Candidate identifiers require independent human verification before publication."
        )
    )
    description = f"An original AromaTwin draft profile for {brand} {name}, generated from supplier availability and candidate matching. This profile requires independent verification before catalogue publication."
    return ProfileDraftCreate(
        supplier_item_id=supplier_id,
        match_candidate_id=candidate_id,
        candidate_brand=brand,
        candidate_fragrance_name=name,
        likely_original_brand=brand,
        likely_original_name=name,
        profile_title=f"{brand} {name}",
        description_original=description,
        description_generation_method="deterministic_supplier_candidate_template_v1",
        confidence_score=confidence,
        source_confidence=source_confidence,
        provenance_notes=provenance,
        review_status=ProfileDraftStatus.needs_human_review,
    )


def generate_profile_drafts(
    suppliers: Iterable[Mapping[str, Any]], candidates: Iterable[Mapping[str, Any]]
) -> list[ProfileDraftCreate]:
    supplier_by_id = {int(row["id"]): row for row in suppliers}
    drafts = []
    for candidate in candidates:
        supplier_id = int(candidate["supplier_item_id"])
        if supplier_id in supplier_by_id:
            drafts.append(generate_profile_draft(supplier_by_id[supplier_id], candidate))
    return drafts


def _evidence_value(record: object, name: str, default: object = None) -> object:
    if isinstance(record, Mapping):
        return record.get(name, default)
    return getattr(record, name, default)


def approval_evidence(records: Iterable[object]) -> list[ApprovalEvidence]:
    return [
        ApprovalEvidence(
            source_name=str(_evidence_value(record, "source_name", "")),
            source_type=str(_evidence_value(record, "source_type", "unknown")).casefold(),
            source_reference=_evidence_value(record, "source_reference"),
            source_url=_evidence_value(record, "source_url"),
            licence_status=str(_evidence_value(record, "licence_status", "unknown")).casefold(),
            commercial_use_allowed=bool(_evidence_value(record, "commercial_use_allowed", False)),
            confidence=float(_evidence_value(record, "confidence", 0)),
        )
        for record in records
    ]


def _apply_updates(draft: Any, updates: dict[str, object]) -> Any:
    if hasattr(draft, "model_copy"):
        return draft.model_copy(update=updates)
    for name, value in updates.items():
        setattr(draft, name, value)
    return draft


def approve_profile_draft(
    draft: Any, decision: ProfileDraftDecisionRequest, evidence_records: Iterable[object]
) -> Any:
    evidence = approval_evidence(evidence_records)
    qualifying = [
        item
        for item in evidence
        if (
            item.source_type in APPROVABLE_SOURCE_TYPES
            or item.licence_status in APPROVABLE_LICENCE_STATUSES
        )
        and item.licence_status in APPROVABLE_LICENCE_STATUSES
        and item.commercial_use_allowed
        and item.confidence >= MINIMUM_APPROVAL_CONFIDENCE
        and (item.source_reference or item.source_url)
    ]
    if not qualifying:
        raise ValueError("Draft lacks trusted, commercially permitted provenance")
    if bool(getattr(draft, "restricted_content_detected", False)):
        raise ValueError("Draft contains restricted or copied content")
    if float(draft.source_confidence) < MINIMUM_APPROVAL_CONFIDENCE:
        raise ValueError("Draft source confidence is below the approval threshold")
    if str(draft.review_status) not in {
        ProfileDraftStatus.needs_human_review,
        ProfileDraftStatus.needs_human_review.value,
    }:
        raise ValueError("Only drafts awaiting human review can be approved")
    now = datetime.now(UTC)
    sources = ", ".join(sorted({item.source_name for item in qualifying}))
    return _apply_updates(
        draft,
        {
            "review_status": ProfileDraftStatus.approved_for_catalogue.value,
            "reviewer": decision.reviewer,
            "approved_at": now,
            "updated_at": now,
            "provenance_notes": f"{draft.provenance_notes} Human approval used trusted provenance: {sources}. Review rationale: {decision.reason}.",
        },
    )


def reject_profile_draft(
    draft: ProfileDraftRead, decision: ProfileDraftDecisionRequest
) -> ProfileDraftRead:
    allowed = {
        ProfileDraftStatus.rejected_low_confidence,
        ProfileDraftStatus.rejected_licensing_risk,
        ProfileDraftStatus.rejected_duplicate,
        ProfileDraftStatus.requires_more_sources,
    }
    status = decision.rejection_status or ProfileDraftStatus.requires_more_sources
    if status not in allowed:
        raise ValueError("Invalid rejection status")
    now = datetime.now(UTC)
    return _apply_updates(
        draft,
        {
            "review_status": status.value,
            "reviewer": decision.reviewer,
            "rejection_reason": decision.reason,
            "rejected_at": now,
            "updated_at": now,
        },
    )


def load_csv_records(path: str) -> list[dict[str, str]]:
    import csv
    from pathlib import Path

    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_profile_drafts_from_files(
    supplier_items_path: str,
    match_candidates_path: str,
    review_queue_path: str | None = None,
    source_provenance_path: str | None = None,
) -> list[ProfileDraftCreate]:
    suppliers = load_csv_records(supplier_items_path)
    candidates = load_csv_records(match_candidates_path)
    if review_queue_path:
        queue = load_csv_records(review_queue_path)
        eligible = {
            int(row["supplier_item_id"])
            for row in queue
            if row.get("queue_status", "needs_profile_draft") == "needs_profile_draft"
        }
        suppliers = [row for row in suppliers if int(row["id"]) in eligible]
    if source_provenance_path:
        provenance = load_csv_records(source_provenance_path)
        confidence_by_candidate = {
            int(row["entity_id"]): row.get("confidence", "0")
            for row in provenance
            if row.get("entity_type") == "match_candidate"
        }
        candidates = [
            {
                **row,
                "match_confidence": confidence_by_candidate.get(
                    int(row["id"]), row.get("match_confidence", "0")
                ),
            }
            for row in candidates
        ]
    return generate_profile_drafts(suppliers, candidates)
