import csv
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from aromatwin.routers.enrichment_reviews import (
    _REVIEWS,
    _SOURCES,
    approve_review,
    generate_enrichment_review,
    mark_ready,
    reject_review,
)
from aromatwin.schemas.enrichment_review import (
    EnrichmentReviewDecisionRequest,
    EnrichmentReviewGenerateRequest,
)
from aromatwin.services.enrichment_review import (
    EnrichmentSource,
    approve_enrichment_review,
    build_enrichment_review,
    mark_enrichment_ready,
)
from scripts.build_enrichment_reviews import OUTPUT_FIELDS, build_rows


def _draft(**overrides: object) -> SimpleNamespace:
    values = {
        "id": 1,
        "brand": "Aster & Vale",
        "fragrance_name": "Moonlit Grove",
        "concentration": "Eau de parfum",
        "review_status": "approved",
        "supplier_price": "99.00",
        "supplier_code": "SECRET",
        "stock": 5,
        "quantity": 12,
        "commercial_terms": "CONFIDENTIAL",
        "description": "THIRD PARTY DESCRIPTION",
        "review": "THIRD PARTY REVIEW",
        "rating": 5,
        "image_url": "PRIVATE IMAGE",
        "comment": "THIRD PARTY COMMENT",
        "ugc": "THIRD PARTY UGC",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _source(**overrides: object) -> EnrichmentSource:
    values = {
        "id": 1,
        "source_name": "Official identity record",
        "source_type": "official",
        "source_reference": "OFFICIAL-1",
        "source_url": "https://example.com/official-1",
        "licence_status": "official-factual-metadata",
        "commercial_use_allowed": True,
        "source_confidence": 0.91,
        "licensing_risk": "low",
        "reference_only": False,
    }
    values.update(overrides)
    return EnrichmentSource(**values)


def _ready_review(**source_overrides: object):
    source = _source(**source_overrides)
    review = build_enrichment_review(_draft(), [source], enrichment_review_id=1)
    return mark_enrichment_ready(review, [source]), source


def setup_function() -> None:
    _REVIEWS.clear()
    _SOURCES.clear()


def test_generation_from_profile_draft_defaults_to_human_review() -> None:
    review = build_enrichment_review(_draft(), [_source()], enrichment_review_id=3)

    assert review.profile_draft_id == 1
    assert review.brand == "Aster & Vale"
    assert review.review_status == "needs_human_review"
    assert review.description_original.startswith("An original AromaTwin enrichment review")


def test_reference_only_source_cannot_be_approved() -> None:
    review, source = _ready_review(source_type="reference_only", reference_only=True)
    review = replace(review, licensing_risk="low")

    with pytest.raises(ValueError, match="Reference-only"):
        approve_enrichment_review(review, [source], "Curator")


def test_mark_ready_and_approval_fail_with_insufficient_provenance() -> None:
    review = build_enrichment_review(_draft(), [], enrichment_review_id=1)

    with pytest.raises(ValueError, match="provenance"):
        mark_enrichment_ready(review, [])
    with pytest.raises(ValueError, match="not ready_for_approval"):
        approve_enrichment_review(review, [], "Curator")


def test_approval_fails_with_low_source_confidence() -> None:
    review, source = _ready_review(source_confidence=0.4)
    with pytest.raises(ValueError, match="too low"):
        approve_enrichment_review(review, [source], "Curator")


def test_approval_fails_with_high_licensing_risk() -> None:
    review, source = _ready_review(licensing_risk="high")
    with pytest.raises(ValueError, match="High licensing risk"):
        approve_enrichment_review(review, [source], "Curator")


def test_approval_fails_when_copied_restricted_content_is_detected() -> None:
    review, source = _ready_review()
    review = replace(review, copied_restricted_content=True)
    with pytest.raises(ValueError, match="Copied restricted content"):
        approve_enrichment_review(review, [source], "Curator")


def test_approval_fails_until_record_is_ready() -> None:
    review = build_enrichment_review(_draft(), [_source()], enrichment_review_id=1)
    with pytest.raises(ValueError, match="not ready_for_approval"):
        approve_enrichment_review(review, [_source()], "Curator")


def test_reject_endpoint_stores_rejection_reason() -> None:
    _SOURCES.append(_source())
    generated = generate_enrichment_review(
        EnrichmentReviewGenerateRequest(
            profile_draft_id=1,
            brand="Aster & Vale",
            fragrance_name="Moonlit Grove",
            concentration="Eau de parfum",
            profile_draft_status="approved",
            source_ids=(1,),
        )
    )
    assert generated.review_status == "needs_human_review"
    rejected = reject_review(
        1,
        EnrichmentReviewDecisionRequest(
            reviewer="Curator", reason="Identity needs stronger evidence"
        ),
    )
    assert rejected.review_status == "rejected"
    assert rejected.rejection_reason == "Identity needs stronger evidence"


def test_router_enforces_readiness_and_approval_rules() -> None:
    _SOURCES.append(_source())
    generate_enrichment_review(
        EnrichmentReviewGenerateRequest(
            profile_draft_id=1,
            brand="Aster & Vale",
            fragrance_name="Moonlit Grove",
            profile_draft_status="approved",
            source_ids=(1,),
        )
    )
    with pytest.raises(HTTPException, match="not ready_for_approval"):
        approve_review(1, EnrichmentReviewDecisionRequest(reviewer="Curator"))
    assert mark_ready(1).review_status == "ready_for_approval"
    assert approve_review(
        1, EnrichmentReviewDecisionRequest(reviewer="Curator")
    ).review_status == "approved_for_catalogue"


def test_enrichment_reviews_csv_has_safe_expected_headers() -> None:
    with Path("data/enrichment_reviews.csv").open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
    assert tuple(reader.fieldnames or ()) == OUTPUT_FIELDS
    assert rows
    assert {row["review_status"] for row in rows} == {"needs_human_review"}
    forbidden = {
        "supplier_price", "aed_price", "usd_price", "supplier_code", "supplier_cn_code",
        "cn_code", "stock", "quantity", "commercial_terms", "review", "rating", "image",
        "comment", "ugc",
    }
    assert forbidden.isdisjoint(reader.fieldnames or ())


def test_public_outputs_exclude_commercial_and_restricted_input_fields(tmp_path: Path) -> None:
    draft_path = tmp_path / "profile_drafts.csv"
    source_path = tmp_path / "sources.csv"
    draft_path.write_text(
        "id,brand,fragrance_name,concentration,review_status,supplier_price,supplier_code,stock,"
        "quantity,commercial_terms,description,review,rating,image_url,comment,ugc\n"
        "1,Aster & Vale,Moonlit Grove,Eau de parfum,approved,99,SECRET,5,12,CONFIDENTIAL,"
        "COPIED DESCRIPTION,COPIED REVIEW,5,PRIVATE IMAGE,COPIED COMMENT,COPIED UGC\n",
        encoding="utf-8",
    )
    source_path.write_text(
        "id,profile_draft_id,source_name,source_type,source_reference,source_url,licence_status,"
        "commercial_use_allowed,source_confidence,licensing_risk,reference_only\n"
        "1,1,Official record,official,REF-1,https://example.com/1,official,true,0.9,low,false\n",
        encoding="utf-8",
    )
    rows = build_rows(draft_path, source_path)
    rendered = " ".join(rows[0].values())
    for restricted_value in (
        "99", "SECRET", "CONFIDENTIAL", "COPIED DESCRIPTION", "COPIED REVIEW",
        "PRIVATE IMAGE", "COPIED COMMENT", "COPIED UGC",
    ):
        assert restricted_value not in rendered
    assert rows[0]["review_status"] == "needs_human_review"
    assert set(rows[0]) == set(OUTPUT_FIELDS)
