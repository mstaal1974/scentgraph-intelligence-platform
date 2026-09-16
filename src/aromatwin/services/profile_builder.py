from dataclasses import dataclass, replace
from typing import Protocol


NEEDS_HUMAN_REVIEW = "needs_human_review"
APPROVAL_CONFIDENCE_THRESHOLD = 0.75
RESTRICTED_SOURCE_TYPES = {"reference_only", "restricted_non_commercial", "unknown"}


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
    description = (
        f"Draft profile for {match_candidate.candidate_brand} "
        f"{match_candidate.candidate_fragrance_name}. "
        "Original descriptive details must be written and verified by a human reviewer."
    )
    provenance = (
        f"Identity proposed by {match_candidate.candidate_source_type} candidate "
        f"{match_candidate.id} from supplier item {supplier_item.id}; descriptive fields were not copied."
    )
    return ProfileDraft(
        id=draft_id,
        supplier_item_id=supplier_item.id,
        match_candidate_id=match_candidate.id,
        brand=match_candidate.candidate_brand,
        fragrance_name=match_candidate.candidate_fragrance_name,
        concentration=match_candidate.candidate_concentration,
        description=description,
        provenance_notes=provenance,
        source_type=match_candidate.candidate_source_type,
        source_confidence=confidence,
    )


def approve_profile_draft(draft: ProfileDraft) -> ProfileDraft:
    if not draft.provenance_notes.strip():
        raise ValueError("Approval requires sufficient provenance")
    if draft.source_type in RESTRICTED_SOURCE_TYPES:
        raise ValueError("Restricted or reference-only content cannot be approved")
    if draft.source_confidence < APPROVAL_CONFIDENCE_THRESHOLD:
        raise ValueError("Source confidence is too low for approval")
    if "descriptive fields were not copied" not in draft.provenance_notes:
        raise ValueError("Provenance does not confirm that copied content was excluded")
    return replace(draft, review_status="approved")


def reject_profile_draft(draft: ProfileDraft, reason: str) -> ProfileDraft:
    if not reason.strip():
        raise ValueError("A rejection reason is required")
    return replace(draft, review_status="rejected", rejection_reason=reason.strip())

