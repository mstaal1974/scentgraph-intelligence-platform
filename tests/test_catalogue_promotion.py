import csv
from pathlib import Path
from types import SimpleNamespace

import pytest

from aromatwin.services.catalogue_promotion import (
    CATALOGUE_FIELDS,
    PRIVATE_SUPPLIER_FIELDS,
    promote_enrichment_review,
)
from scripts.promote_catalogue_records import promote_rows


def review(**overrides: object) -> SimpleNamespace:
    values = {
        "id": 7,
        "profile_draft_id": 3,
        "brand": "Aster & Vale",
        "fragrance_name": "Moonlit Grove",
        "concentration": "Eau de parfum",
        "description_original": "An original, human-reviewed woodland profile.",
        "provenance_summary": "Identity verified from licensed first-party facts.",
        "source_ids": (11,),
        "source_confidence": 0.9,
        "licensing_risk": "low",
        "copied_restricted_content": False,
        "review_status": "approved_for_catalogue",
        "reviewer": "Curator",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_approved_enrichment_review_can_be_promoted() -> None:
    item = promote_enrichment_review(review())
    assert item.brand_slug == "aster-vale"
    assert item.slug == "moonlit-grove"
    assert item.provenance_references == (11,)


@pytest.mark.parametrize(
    "status",
    ["needs_human_review", "requires_more_sources", "rejected_low_confidence",
     "rejected_licensing_risk", "rejected_duplicate", "approved"],
)
def test_non_approved_enrichment_review_cannot_be_promoted(status: str) -> None:
    with pytest.raises(ValueError, match="approved_for_catalogue"):
        promote_enrichment_review(review(review_status=status))


@pytest.mark.parametrize("record_type", ["profile_draft", "supplier_item", "match_candidate"])
def test_non_review_record_cannot_be_promoted(record_type: str) -> None:
    with pytest.raises(ValueError, match="Only enrichment reviews"):
        promote_enrichment_review(review(record_type=record_type))


def test_promotion_fails_with_low_source_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        promote_enrichment_review(review(source_confidence=0.74))


@pytest.mark.parametrize("confidence", ["nan", "inf", "not-a-number"])
def test_promotion_fails_with_invalid_source_confidence(confidence: str) -> None:
    with pytest.raises(ValueError, match="confidence"):
        promote_enrichment_review(review(source_confidence=confidence))


def test_promotion_fails_with_high_licensing_risk() -> None:
    with pytest.raises(ValueError, match="licensing"):
        promote_enrichment_review(review(licensing_risk="high"))


def test_promotion_fails_with_restricted_content() -> None:
    with pytest.raises(ValueError, match="Copied restricted"):
        promote_enrichment_review(review(copied_restricted_content=True))


def test_supplier_private_input_is_rejected_and_output_is_allowlisted() -> None:
    with pytest.raises(ValueError, match="Supplier-private"):
        promote_enrichment_review(review(supplier_price="99.00"))
    item = promote_enrichment_review(review())
    assert PRIVATE_SUPPLIER_FIELDS.isdisjoint(vars(item))


@pytest.mark.parametrize("field,value", [("stock", 0), ("SUPPLIER_CODE", "private")])
def test_supplier_private_fields_are_rejected_even_when_zero_or_uppercase(
    field: str, value: object
) -> None:
    with pytest.raises(ValueError, match="Supplier-private"):
        promote_enrichment_review(review(**{field: value}))


def test_truthy_csv_restricted_content_flag_is_rejected() -> None:
    with pytest.raises(ValueError, match="Copied restricted"):
        promote_enrichment_review(review(copied_restricted_content="yes"))


def test_duplicate_promotion_is_idempotent_and_identity_collision_is_rejected() -> None:
    first = promote_enrichment_review(review())
    assert promote_enrichment_review(review(), [first]) is first
    with pytest.raises(ValueError, match="already exists"):
        promote_enrichment_review(review(id=8), [first])


def test_catalogue_csv_has_expected_public_safe_headers() -> None:
    with Path("data/catalogue_fragrances.csv").open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        assert tuple(reader.fieldnames or ()) == CATALOGUE_FIELDS
        assert list(reader)
    assert PRIVATE_SUPPLIER_FIELDS.isdisjoint(reader.fieldnames or ())


def test_cli_promotes_only_valid_approved_rows(tmp_path: Path) -> None:
    source = tmp_path / "reviews.csv"
    output = tmp_path / "catalogue.csv"
    fields = list(vars(review()))
    rows = [vars(review()), vars(review(id=8, review_status="needs_human_review"))]
    with source.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    accepted, rejected = promote_rows(source, output)
    assert (accepted, rejected) == (1, 1)
    assert "Moonlit Grove" in output.read_text(encoding="utf-8")


def test_missing_provenance_or_human_reviewer_is_rejected() -> None:
    with pytest.raises(ValueError, match="provenance"):
        promote_enrichment_review(review(source_ids=()))
    with pytest.raises(ValueError, match="reviewer"):
        promote_enrichment_review(review(reviewer=""))
