from dataclasses import asdict

from aromatwin.config import Settings
from aromatwin.main import create_app
from aromatwin.services.bulk_profile_generation import (
    generate_bulk_profile_drafts,
    public_safe_draft,
)


def offer(identifier, supplier="A", reference="REF"):
    return {"id": identifier, "supplier_name": supplier, "supplier_brand_raw": "Fictional",
            "supplier_name_raw": "Rain Glass", "supplier_reference_raw": reference,
            "price_aed_private": "secret", "supplier_code_private": "secret"}


def test_groups_offers_and_outputs_review_only_public_safe_draft():
    result = generate_bulk_profile_drafts([offer(1), offer(2, "B")])
    assert result.unique_candidate_count == 1
    assert result.accepted_count == 1
    assert result.skipped_duplicate_count == 1
    draft = result.drafts[0]
    assert draft.review_status == "needs_human_review"
    assert draft.enrichment_needed
    assert set(draft.missing_profile_fields) >= {"notes", "accords", "moods", "seasons"}
    assert "independent verification" in draft.draft_description
    serialized = str(public_safe_draft(draft)).casefold()
    for forbidden in ("price", "supplier_code", "cn_code", "quantity", "stock", "margin",
                      "review", "rating", "image", "comment", "ugc"):
        if forbidden == "review":
            continue
        assert forbidden not in serialized


def test_existing_draft_prevents_duplicate_and_fatma_missing_reference_lowers_confidence():
    fatma = offer(1, reference=None)
    first = generate_bulk_profile_drafts([fatma])
    assert first.drafts[0].source_confidence <= 0.55
    assert "missing" in first.drafts[0].confidence_reason.casefold()
    assert generate_bulk_profile_drafts([fatma], existing_drafts=first.drafts).drafts == []
    assert "approved" not in asdict(first.drafts[0]).values()


def test_openapi_exposes_internal_bulk_profile_endpoints():
    schema = create_app(Settings(enable_private_supplier_endpoints=True)).openapi()
    expected = {"/bulk-profiles/health", "/bulk-profiles/generate",
                "/bulk-profiles/coverage", "/bulk-profiles/research-queue"}
    assert expected <= set(schema["paths"])
