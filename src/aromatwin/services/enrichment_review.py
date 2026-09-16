"""Independent, review-only enrichment of profile drafts.

There is deliberately no catalogue-writing operation here. Public records are built from an
allowlist so supplier commercial data and third-party descriptive content cannot leak.
"""

import csv
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping, Protocol, Sequence

NEEDS_HUMAN_REVIEW = "needs_human_review"
READY_FOR_APPROVAL = "ready_for_approval"
APPROVED = "approved_for_catalogue"
PROFILE_APPROVED = "approved"
REJECTED = "rejected"
APPROVAL_CONFIDENCE_THRESHOLD = 0.75
RESTRICTED_SOURCE_TYPES = {"reference_only", "restricted_non_commercial", "unknown"}


def _normalise(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


class ProfileDraftLike(Protocol):
    id: int
    brand: str
    fragrance_name: str
    concentration: str | None
    review_status: str


@dataclass(frozen=True)
class EnrichmentSource:
    id: int
    source_name: str
    source_type: str
    source_reference: str
    source_url: str | None
    licence_status: str
    commercial_use_allowed: bool
    source_confidence: float
    licensing_risk: str
    reference_only: bool = False


@dataclass(frozen=True)
class EnrichmentReview:
    id: int
    profile_draft_id: int
    brand: str
    fragrance_name: str
    concentration: str | None
    description_original: str
    provenance_summary: str
    source_ids: tuple[int, ...]
    source_confidence: float
    licensing_risk: str
    copied_restricted_content: bool = False
    review_status: str = NEEDS_HUMAN_REVIEW
    reviewer: str | None = None
    rejection_reason: str | None = None


def original_enrichment_description(brand: str, name: str) -> str:
    """Produce deterministic original copy rather than importing source descriptions."""
    return (
        f"An original AromaTwin enrichment review for {brand} {name}, prepared from supplier "
        "availability, candidate matching, and recorded source metadata. This profile requires "
        "human review before catalogue publication."
    )


def _source_is_restricted(source: EnrichmentSource) -> bool:
    return source.reference_only or _normalise(source.source_type) in RESTRICTED_SOURCE_TYPES


def provenance_is_sufficient(sources: Sequence[EnrichmentSource]) -> bool:
    return bool(sources) and all(
        source.source_name.strip()
        and source.source_reference.strip()
        and source.licence_status.strip()
        for source in sources
    )


def _provenance_summary(sources: Sequence[EnrichmentSource]) -> str:
    if not sources:
        return "No independently recorded sources; provenance review required."
    labels = ", ".join(f"{source.source_name} ({source.source_type})" for source in sources)
    return (
        f"Independent source metadata recorded from {labels}. Only identity and provenance "
        "metadata were used; descriptions, reviews, ratings, images, comments, and UGC were "
        "not copied."
    )


def build_enrichment_review(
    draft: ProfileDraftLike,
    sources: Sequence[EnrichmentSource],
    *,
    enrichment_review_id: int = 0,
) -> EnrichmentReview:
    """Build a record from allowlisted draft identity and source metadata only."""
    if _normalise(draft.review_status) not in {
        NEEDS_HUMAN_REVIEW,
        READY_FOR_APPROVAL,
        APPROVED,
        PROFILE_APPROVED,
    }:
        raise ValueError("Profile draft is not approved or review-ready")
    brand = draft.brand.strip()
    name = draft.fragrance_name.strip()
    if not brand or not name:
        raise ValueError("Profile draft brand and fragrance name are required")
    confidence = min((source.source_confidence for source in sources), default=0.0)
    confidence = max(0.0, min(1.0, float(confidence)))
    licensing_risk = "high" if any(
        _normalise(source.licensing_risk) == "high"
        or _source_is_restricted(source)
        or not source.commercial_use_allowed
        for source in sources
    ) else "low"
    return EnrichmentReview(
        id=enrichment_review_id,
        profile_draft_id=draft.id,
        brand=brand,
        fragrance_name=name,
        concentration=draft.concentration,
        description_original=original_enrichment_description(brand, name),
        provenance_summary=_provenance_summary(sources),
        source_ids=tuple(source.id for source in sources),
        source_confidence=confidence,
        licensing_risk=licensing_risk,
    )


def mark_enrichment_ready(
    review: EnrichmentReview, sources: Sequence[EnrichmentSource]
) -> EnrichmentReview:
    if not provenance_is_sufficient(sources):
        raise ValueError("Sufficient provenance is required before marking ready")
    return replace(review, review_status=READY_FOR_APPROVAL)


def approve_enrichment_review(
    review: EnrichmentReview, sources: Sequence[EnrichmentSource], reviewer: str
) -> EnrichmentReview:
    if review.review_status != READY_FOR_APPROVAL:
        raise ValueError("Enrichment review is not ready_for_approval")
    if not provenance_is_sufficient(sources):
        raise ValueError("Approval requires sufficient provenance")
    if review.source_confidence < APPROVAL_CONFIDENCE_THRESHOLD:
        raise ValueError("Source confidence is too low for approval")
    if _normalise(review.licensing_risk) == "high":
        raise ValueError("High licensing risk prevents approval")
    if review.copied_restricted_content:
        raise ValueError("Copied restricted content prevents approval")
    if any(_source_is_restricted(source) or not source.commercial_use_allowed for source in sources):
        raise ValueError("Reference-only sources cannot be promoted directly")
    if review.description_original != original_enrichment_description(
        review.brand, review.fragrance_name
    ):
        raise ValueError("Copied restricted content prevents approval")
    return replace(review, review_status=APPROVED, reviewer=reviewer.strip())


def reject_enrichment_review(
    review: EnrichmentReview, reason: str, reviewer: str
) -> EnrichmentReview:
    if not reason.strip():
        raise ValueError("A rejection reason is required")
    return replace(
        review,
        review_status=REJECTED,
        reviewer=reviewer.strip(),
        rejection_reason=reason.strip(),
    )


def load_profile_drafts(path: Path) -> list[dict[str, str]]:
    """Load draft rows while retaining only fields required by enrichment."""
    allowed = ("id", "brand", "fragrance_name", "concentration", "review_status")
    with path.open(newline="", encoding="utf-8-sig") as source:
        return [{key: row.get(key, "") for key in allowed} for row in csv.DictReader(source)]


def contains_restricted_input(row: Mapping[str, object]) -> bool:
    """Report restricted payload fields; callers must never copy their values."""
    restricted = {"description", "review", "rating", "image", "image_url", "comment", "ugc"}
    return any(row.get(field) not in (None, "", []) for field in restricted)
