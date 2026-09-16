import pytest

from aromatwin.services.enrichment import EnrichmentProposal, approve_enrichment
from aromatwin.services.provenance import (
    PermittedUse,
    SourcePolicy,
    restricted_reference_policy,
    validate_commercial_promotion,
    validate_matching_use,
)


def proposal() -> EnrichmentProposal:
    return EnrichmentProposal(
        match_candidate_id=1,
        approved_brand="Brand",
        approved_fragrance_name="Scent",
        official_source_url="https://brand.example/scent",
        description_original="An original description.",
        description_ai_generated=True,
        description_reviewed=True,
        source_confidence=0.8,
    )


def test_restricted_source_is_allowed_for_matching_only() -> None:
    policy = restricted_reference_policy("Non-commercial sample")
    validate_matching_use(policy)
    with pytest.raises(ValueError, match="cannot be promoted"):
        validate_commercial_promotion(policy)


def test_restricted_reference_cannot_promote_catalogue_record() -> None:
    with pytest.raises(ValueError, match="cannot be promoted"):
        approve_enrichment(proposal(), restricted_reference_policy("Reference"), "Reviewer")


def test_licensed_source_can_support_reviewed_promotion() -> None:
    policy = SourcePolicy(
        "Licensed source",
        "dataset",
        PermittedUse.licensed_commercial,
        commercial_use_allowed=True,
        can_use_for_matching=True,
    )
    approved = approve_enrichment(proposal(), policy, "Reviewer")
    assert approved.review_status == "approved_for_catalogue"
    assert approved.reviewer == "Reviewer"


def test_noncommercial_source_cannot_enable_copying() -> None:
    with pytest.raises(ValueError, match="cannot permit"):
        SourcePolicy(
            "Unsafe", "dataset", PermittedUse.restricted_non_commercial, can_copy_text=True
        )
