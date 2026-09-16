from dataclasses import dataclass, replace
from typing import Protocol


NEEDS_HUMAN_REVIEW = "needs_human_review"
APPROVAL_CONFIDENCE_THRESHOLD = 0.75
RESTRICTED_SOURCE_TYPES = {"reference_only", "restricted_non_commercial", "unknown"}


def _normalise_source_type(source_type: str) -> str:
    return source_type.strip().lower().replace("-", "_").replace(" ", "_")


def draft_description(brand: str, name: str) -> str:
    """Return original, deterministic placeholder copy for a draft identity."""
    return (
        f"An original AromaTwin draft profile for {brand} {name}, generated from supplier "
        "availability and candidate matching. This profile requires independent verification "
        "before catalogue publication."
    )


def draft_provenance_notes(
    *, supplier_item_id: int, match_candidate_id: int, source_type: str
) -> str:
    """Describe the permitted identity inputs without reproducing source material."""
    return (
        f"Identity proposed by {source_type} candidate {match_candidate_id} from supplier item "
        f"{supplier_item_id}; only identity fields and confidence were used; third-party "
        "descriptions, reviews, ratings, images, comments, and UGC were not copied."
    )


class SupplierItemLike(Protocol):
    id: int
    normalised_brand: str
    normalised_name: str


class MatchCandidateLike(Protocol):
    id: int
    supplier_item_id: int
    candidate_brand: str
    candidate_fragrance_name: str
    candidate_concentration: str | None
    candidate_source_type: str
    candidate_source_reference: str | None
    match_confidence: float


@dataclass(frozen=True)
class ProfileDraft:
    id: int
    supplier_item_id: int
    match_candidate_id: int
    brand: str
    fragrance_name: str
    concentration: str | None
    description: str
    provenance_notes: str
    source_type: str
    source_confidence: float
    review_status: str = NEEDS_HUMAN_REVIEW
    rejection_reason: str | None = None


def build_profile_draft(
    supplier_item: SupplierItemLike, match_candidate: MatchCandidateLike, *, draft_id: int = 0
) -> ProfileDraft:
    """Build a safe draft using identity metadata, never copied descriptive content."""
    if match_candidate.supplier_item_id != supplier_item.id:
        raise ValueError("Match candidate does not belong to the supplier item")

    confidence = max(0.0, min(1.0, float(match_candidate.match_confidence)))
    brand = match_candidate.candidate_brand.strip()
    fragrance_name = match_candidate.candidate_fragrance_name.strip()
    source_type = _normalise_source_type(match_candidate.candidate_source_type)
    if not brand or not fragrance_name:
        raise ValueError("Candidate brand and fragrance name are required")
    description = draft_description(brand, fragrance_name)
    provenance = draft_provenance_notes(
        supplier_item_id=supplier_item.id,
        match_candidate_id=match_candidate.id,
        source_type=source_type,
    )
    return ProfileDraft(
        id=draft_id,
        supplier_item_id=supplier_item.id,
        match_candidate_id=match_candidate.id,
        brand=brand,
        fragrance_name=fragrance_name,
        concentration=match_candidate.candidate_concentration,
        description=description,
        provenance_notes=provenance,
        source_type=source_type,
        source_confidence=confidence,
    )


def approve_profile_draft(draft: ProfileDraft) -> ProfileDraft:
    if not draft.provenance_notes.strip():
        raise ValueError("Approval requires sufficient provenance")
    if _normalise_source_type(draft.source_type) in RESTRICTED_SOURCE_TYPES:
        raise ValueError("Restricted or reference-only content cannot be approved")
    if draft.source_confidence < APPROVAL_CONFIDENCE_THRESHOLD:
        raise ValueError("Source confidence is too low for approval")
    expected_description = draft_description(draft.brand, draft.fragrance_name)
    expected_provenance = draft_provenance_notes(
        supplier_item_id=draft.supplier_item_id,
        match_candidate_id=draft.match_candidate_id,
        source_type=draft.source_type,
    )
    if draft.description != expected_description or draft.provenance_notes != expected_provenance:
        raise ValueError("Restricted, reference-only, or copied content was detected")
    return replace(draft, review_status="approved")


def reject_profile_draft(draft: ProfileDraft, reason: str) -> ProfileDraft:
    if not reason.strip():
        raise ValueError("A rejection reason is required")
    return replace(draft, review_status="rejected", rejection_reason=reason.strip())
