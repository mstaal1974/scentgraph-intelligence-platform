from __future__ import annotations
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aromatwin.schemas.enrichment import EnrichmentDecisionRequest, EnrichmentReviewCreate

MINIMUM_READY_CONFIDENCE = 0.7
RESTRICTED_SOURCE_TYPES = frozenset({"reference_only", "restricted_non_commercial", "unknown"})


@dataclass(frozen=True)
class SourceFacts:
    id: int
    source_name: str
    source_type: str
    source_url: str | None
    commercial_use_allowed: bool
    can_copy_text: bool
    can_use_for_factual_reference: bool
    source_confidence: float


@dataclass(frozen=True)
class EnrichmentEventData:
    profile_draft_id: int
    event_type: str
    event_summary: str
    actor: str


def _value(record: object, name: str, default: object = None) -> object:
    if isinstance(record, Mapping):
        return record.get(name, default)
    return getattr(record, name, default)


def source_facts(records: Iterable[object]) -> list[SourceFacts]:
    return [
        SourceFacts(
            id=int(_value(item, "id")),
            source_name=str(_value(item, "source_name", "")),
            source_type=str(_value(item, "source_type", "unknown")).casefold(),
            source_url=str(_value(item, "source_url")) if _value(item, "source_url") else None,
            commercial_use_allowed=bool(_value(item, "commercial_use_allowed", False)),
            can_copy_text=bool(_value(item, "can_copy_text", False)),
            can_use_for_factual_reference=bool(
                _value(item, "can_use_for_factual_reference", False)
            ),
            source_confidence=float(_value(item, "source_confidence", 0)),
        )
        for item in records
    ]


def assess_sources(records: Iterable[object]) -> tuple[float, str, str]:
    sources = source_facts(records)
    usable = [
        source
        for source in sources
        if source.can_use_for_factual_reference
        and source.source_type not in RESTRICTED_SOURCE_TYPES
    ]
    confidence = max((source.source_confidence for source in usable), default=0.0)
    if not usable:
        return confidence, "high", "No independently usable factual source is linked."
    commercially_permitted = [source for source in usable if source.commercial_use_allowed]
    if not commercially_permitted:
        return (
            confidence,
            "medium",
            "Sources support factual review but commercial permission is not documented.",
        )
    return (
        confidence,
        "low",
        "Independently recorded factual source metadata is linked; human verification remains required.",
    )


def generate_enrichment_review(
    profile: object, linked_sources: Iterable[object] = ()
) -> EnrichmentReviewCreate:
    from aromatwin.schemas.enrichment import EnrichmentReviewCreate

    brand = str(_value(profile, "candidate_brand", ""))
    fragrance = str(_value(profile, "candidate_fragrance_name", ""))
    profile_id = int(_value(profile, "id"))
    confidence, risk, summary = assess_sources(linked_sources)
    description = f"An original AromaTwin draft profile for {brand} {fragrance}, prepared from supplier availability, candidate matching, and independently recorded source metadata. This profile requires human review before catalogue publication."
    return EnrichmentReviewCreate(
        profile_draft_id=profile_id,
        approved_brand=brand,
        approved_fragrance_name=fragrance,
        source_summary=summary,
        description_original=description,
        note_pyramid_json={"top": [], "heart": [], "base": []},
        enrichment_confidence=round(confidence, 3),
        licensing_risk=risk,
        copied_text_detected=False,
        review_status="needs_human_review",
    )


def _apply(record: Any, updates: dict[str, object]) -> Any:
    if hasattr(record, "model_copy"):
        return record.model_copy(update=updates)
    for name, value in updates.items():
        setattr(record, name, value)
    return record


def validate_ready(review: object, sources: Iterable[object]) -> None:
    facts = source_facts(sources)
    confidence = float(_value(review, "enrichment_confidence", 0))
    risk = str(_value(review, "licensing_risk", "high"))
    copied = bool(_value(review, "copied_text_detected", False))
    if confidence < MINIMUM_READY_CONFIDENCE:
        raise ValueError("Enrichment confidence is below the approval threshold")
    if risk != "low":
        raise ValueError("Licensing risk must be low")
    if not facts or any(not source.can_use_for_factual_reference for source in facts):
        raise ValueError("All linked sources must permit factual reference")
    if not any(source.commercial_use_allowed and source.source_url for source in facts):
        raise ValueError("A commercially permitted source URL is required")
    if copied and any(not source.can_copy_text for source in facts):
        raise ValueError("Copied text is prohibited by a linked source")


def mark_ready(
    review: Any, sources: Iterable[object], actor: str
) -> tuple[Any, EnrichmentEventData]:
    validate_ready(review, sources)
    if str(_value(review, "review_status")) not in {
        "needs_human_review",
        "needs_source_review",
        "needs_human_review",
        "needs_source_review",
    }:
        raise ValueError("Review is not eligible to be marked ready")
    now = datetime.now(UTC)
    updated = _apply(
        review, {"review_status": "ready_for_approval", "reviewer": actor, "updated_at": now}
    )
    return updated, EnrichmentEventData(
        int(_value(review, "profile_draft_id")),
        "marked_ready",
        "Enrichment passed source and licensing checks; human approval is still required.",
        actor,
    )


def approve_enrichment_review(
    review: Any, sources: Iterable[object], decision: EnrichmentDecisionRequest
) -> tuple[Any, EnrichmentEventData]:
    if str(_value(review, "review_status")) not in {
        "ready_for_approval",
        "ready_for_approval",
    }:
        raise ValueError("Review must be ready_for_approval")
    validate_ready(review, sources)
    now = datetime.now(UTC)
    updated = _apply(
        review,
        {
            "review_status": "approved_for_catalogue",
            "reviewer": decision.reviewer,
            "review_notes": decision.reason,
            "approved_at": now,
            "description_reviewed": True,
            "official_source_url": next(
                source.source_url
                for source in source_facts(sources)
                if source.commercial_use_allowed and source.source_url
            ),
            "updated_at": now,
        },
    )
    return updated, EnrichmentEventData(
        int(_value(review, "profile_draft_id")),
        "approved",
        "Human reviewer approved enrichment; catalogue promotion remains a separate step.",
        decision.reviewer,
    )


def reject_enrichment(
    review: Any, decision: EnrichmentDecisionRequest
) -> tuple[Any, EnrichmentEventData]:
    allowed = {
        "rejected_low_confidence",
        "rejected_licensing_risk",
        "rejected_duplicate",
        "requires_more_sources",
    }
    status = decision.rejection_status or "requires_more_sources"
    if status not in allowed:
        raise ValueError("Invalid rejection status")
    now = datetime.now(UTC)
    updated = _apply(
        review,
        {
            "review_status": status.value,
            "reviewer": decision.reviewer,
            "review_notes": decision.reason,
            "rejected_at": now,
            "updated_at": now,
        },
    )
    return updated, EnrichmentEventData(
        int(_value(review, "profile_draft_id")),
        "rejected",
        f"Enrichment rejected: {decision.reason}",
        decision.reviewer,
    )


@dataclass(frozen=True)
class EnrichmentProposal:
    match_candidate_id: int
    approved_brand: str
    approved_fragrance_name: str
    official_source_url: str | None
    description_original: str | None
    description_ai_generated: bool
    description_reviewed: bool
    review_status: str = "needs_verification"
    reviewer: str | None = None
    approved_at: datetime | None = None
    source_confidence: float = 0.0


def approve_enrichment(
    proposal: EnrichmentProposal, policy: object, reviewer: str
) -> EnrichmentProposal:
    """Backward-compatible policy approval for the original enrichment boundary."""
    from dataclasses import replace
    from aromatwin.services.provenance import validate_commercial_promotion

    validate_commercial_promotion(policy)
    if not proposal.official_source_url:
        raise ValueError("An official or permitted commercial source URL is required")
    if not proposal.description_reviewed:
        raise ValueError("Original or AI-generated description must be reviewed")
    if not 0 <= proposal.source_confidence <= 1:
        raise ValueError("Source confidence must be between 0 and 1")
    return replace(
        proposal,
        review_status="approved_for_catalogue",
        reviewer=reviewer,
        approved_at=datetime.now(UTC),
    )
