import csv
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException

from aromatwin.routers.profile_drafts import (
    _DRAFTS,
    approve_draft,
    generate_profile_draft,
    reject_draft,
)
from aromatwin.schemas.profile_draft import (
    ProfileDraftDecisionRequest,
    ProfileDraftGenerateRequest,
)
from aromatwin.services.profile_builder import approve_profile_draft, build_profile_draft
from scripts.build_profile_drafts import OUTPUT_FIELDS, build_rows


def _supplier() -> SimpleNamespace:
    return SimpleNamespace(
        id=10, normalised_brand="supplier brand", normalised_name="supplier item"
    )


def _candidate(**overrides: object) -> SimpleNamespace:
    values = {
        "id": 20,
        "supplier_item_id": 10,
        "candidate_brand": "Aster & Vale",
        "candidate_fragrance_name": "Moonlit Grove",
        "candidate_concentration": "Eau de parfum",
        "candidate_source_type": "licensed_commercial",
        "candidate_source_reference": "licensed-record-20",
        "match_confidence": 0.9,
        # These hostile/reference-only fields must never be copied by the builder.
        "description": "THIRD PARTY DESCRIPTION",
        "review": "THIRD PARTY REVIEW",
        "rating": 5,
        "image_url": "https://reference.invalid/image.jpg",
        "comment": "THIRD PARTY COMMENT",
        "ugc": "THIRD PARTY UGC",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _generate_payload(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "supplier_item_id": 10,
        "match_candidate_id": 20,
        "supplier_brand": "private supplier brand",
        "supplier_name": "private supplier item",
        "candidate_brand": "Aster & Vale",
        "candidate_fragrance_name": "Moonlit Grove",
        "candidate_concentration": "Eau de parfum",
        "candidate_source_type": "licensed_commercial",
        "candidate_source_reference": "licensed-record-20",
        "match_confidence": 0.9,
    }
    values.update(overrides)
    return values


def setup_function() -> None:
    _DRAFTS.clear()


def test_draft_generation_from_supplier_item_and_match_candidate() -> None:
    draft = build_profile_draft(_supplier(), _candidate(), draft_id=1)

    assert draft.supplier_item_id == 10
    assert draft.match_candidate_id == 20
    assert draft.brand == "Aster & Vale"
    assert draft.source_confidence == 0.9
    assert draft.review_status == "needs_human_review"


def test_builder_does_not_copy_restricted_content_fields() -> None:
    draft = build_profile_draft(_supplier(), _candidate(), draft_id=1)
    rendered = " ".join((draft.description, draft.provenance_notes))

    assert "THIRD PARTY" not in rendered
    assert "reference.invalid" not in rendered
    assert draft.description == (
        "An original AromaTwin draft profile for Aster & Vale Moonlit Grove, generated from "
        "supplier availability and candidate matching. This profile requires independent "
        "verification before catalogue publication."
    )


def test_restricted_or_reference_only_source_cannot_be_approved() -> None:
    draft = build_profile_draft(
        _supplier(), _candidate(candidate_source_type="reference_only"), draft_id=1
    )

    try:
        approve_profile_draft(draft)
    except ValueError as error:
        assert "reference-only" in str(error)
    else:
        raise AssertionError("Reference-only draft was approved")


def test_approve_endpoint_rejects_insufficient_provenance() -> None:
    draft = build_profile_draft(_supplier(), _candidate(), draft_id=1)
    _DRAFTS.append(replace(draft, provenance_notes=""))

    try:
        approve_draft(1, ProfileDraftDecisionRequest(reviewer="Curator"))
    except HTTPException as error:
        assert error.status_code == 422
        assert "provenance" in str(error.detail).lower()
    else:
        raise AssertionError("Draft with insufficient provenance was approved")


def test_reject_endpoint_stores_rejection_reason() -> None:
    generated = generate_profile_draft(ProfileDraftGenerateRequest(**_generate_payload()))
    assert generated.review_status == "needs_human_review"

    rejected = reject_draft(
        1,
        ProfileDraftDecisionRequest(reviewer="Curator", reason="Identity needs stronger evidence"),
    )

    assert rejected.review_status == "rejected"
    assert rejected.rejection_reason == "Identity needs stronger evidence"


def test_public_profile_draft_excludes_supplier_commercial_fields() -> None:
    draft = generate_profile_draft(ProfileDraftGenerateRequest(**_generate_payload()))
    payload = draft.__dict__

    forbidden = {
        "supplier_name",
        "supplier_brand",
        "supplier_code",
        "supplier_cn_code",
        "price",
        "aed_price",
        "usd_price",
        "stock",
        "quantity",
        "commercial_terms",
    }
    assert forbidden.isdisjoint(payload)
    assert payload["review_status"] == "needs_human_review"


def test_approve_endpoint_rejects_copied_content() -> None:
    draft = build_profile_draft(_supplier(), _candidate(), draft_id=1)
    _DRAFTS.append(replace(draft, description="THIRD PARTY DESCRIPTION"))

    try:
        approve_draft(1, ProfileDraftDecisionRequest(reviewer="Curator"))
    except HTTPException as error:
        assert error.status_code == 422
        assert "copied content" in str(error.detail)
    else:
        raise AssertionError("Draft containing copied content was approved")


def test_profile_drafts_csv_has_safe_expected_headers() -> None:
    path = Path("data/profile_drafts.csv")
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        rows = list(reader)

    assert tuple(reader.fieldnames or ()) == OUTPUT_FIELDS
    assert rows
    assert {row["review_status"] for row in rows} == {"needs_human_review"}
    forbidden_headers = {
        "supplier_price",
        "supplier_code",
        "supplier_cn_code",
        "aed_price",
        "usd_price",
        "stock",
        "quantity",
        "commercial_terms",
    }
    assert forbidden_headers.isdisjoint(reader.fieldnames or ())


def test_csv_builder_allowlists_output_and_ignores_restricted_fields(tmp_path: Path) -> None:
    supplier_path = tmp_path / "supplier_items.csv"
    candidate_path = tmp_path / "match_candidates.csv"
    supplier_path.write_text(
        "id,normalised_brand,normalised_name,aed_price,supplier_code,stock,quantity,commercial_terms\n"
        "10,Private Brand,Private Item,99.00,SECRET,4,12,CONFIDENTIAL\n",
        encoding="utf-8",
    )
    candidate_path.write_text(
        "id,supplier_item_id,candidate_brand,candidate_fragrance_name,"
        "candidate_concentration,candidate_source_type,candidate_source_reference,"
        "match_confidence,description,review,rating,image_url,comment,ugc\n"
        "20,10,Aster & Vale,Moonlit Grove,Eau de parfum,licensed_commercial,ref-20,"
        "0.9,THIRD PARTY DESCRIPTION,THIRD PARTY REVIEW,5,PRIVATE IMAGE,PRIVATE COMMENT,"
        "THIRD PARTY UGC\n",
        encoding="utf-8",
    )

    rows = build_rows(supplier_path, candidate_path)

    assert len(rows) == 1
    assert tuple(rows[0]) == OUTPUT_FIELDS
    assert rows[0]["review_status"] == "needs_human_review"
    rendered = " ".join(rows[0].values())
    for restricted_value in (
        "99.00",
        "SECRET",
        "CONFIDENTIAL",
        "THIRD PARTY DESCRIPTION",
        "THIRD PARTY REVIEW",
        "PRIVATE IMAGE",
        "PRIVATE COMMENT",
        "THIRD PARTY UGC",
    ):
        assert restricted_value not in rendered
