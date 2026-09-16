from dataclasses import dataclass, replace
from datetime import UTC, datetime

from aromatwin.services.provenance import SourcePolicy, validate_commercial_promotion


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
    proposal: EnrichmentProposal, policy: SourcePolicy, reviewer: str
) -> EnrichmentProposal:
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


def reject_enrichment(
    proposal: EnrichmentProposal, reviewer: str, licensing_risk: bool = False
) -> EnrichmentProposal:
    status = "rejected_licensing_risk" if licensing_risk else "rejected_low_confidence"
    return replace(proposal, review_status=status, reviewer=reviewer)
