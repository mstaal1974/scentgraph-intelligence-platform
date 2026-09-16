import csv
from dataclasses import replace
from pathlib import Path

import pytest

from aromatwin.services.catalogue_promotion import PRIVATE_SUPPLIER_FIELDS
from aromatwin.services.recommendation_engine import (
    PUBLIC_RECOMMENDATION_FIELDS,
    approve_recommendation,
    contextual_recommendations,
    generate_recommendations,
    public_recommendation,
)
from aromatwin.services.scent_vector_engine import VECTOR_DIMENSIONS, ScentVector
from scripts.build_recommendations import OUTPUT_FIELDS, build_recommendations


def fragrance(identifier: int, **changes: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": identifier,
        "record_type": "catalogue_fragrance",
        "approved": True,
        "family": "woody",
        "mood": "calm",
        "occasion": "day",
        "season": "spring",
        "accords": "green,fresh",
        "intensity": 0.5,
        "provenance_references": (1,),
    }
    record.update(changes)
    return record


def vector(
    identifier: int,
    *,
    woody: float = 0.8,
    fresh: float = 0.6,
    status: str = "approved",
    confidence: float = 0.9,
) -> ScentVector:
    values = dict.fromkeys(VECTOR_DIMENSIONS, 0.0)
    values.update(woody=woody, fresh=fresh, projection=0.5)
    return ScentVector(identifier, identifier, values, confidence, "test", status, (1,), "safe")


def test_approved_catalogue_generates_ranked_duplicate_safe_recommendations() -> None:
    catalogue = [fragrance(1), fragrance(2), fragrance(3, family="floral")]
    vectors = [vector(1), vector(2, woody=0.79), vector(3, woody=0.1, fresh=0.9)]
    results = generate_recommendations(catalogue[0], catalogue, vectors)
    assert results
    assert all(item.recommended_fragrance_id != 1 and 0 <= item.score <= 1 for item in results)
    assert results[0].recommended_fragrance_id == 2
    assert generate_recommendations(catalogue[0], catalogue, vectors, results) == results


@pytest.mark.parametrize("record_type", ["supplier_item", "profile_draft", "enrichment_review"])
def test_workflow_records_cannot_generate_public_recommendations(record_type: str) -> None:
    with pytest.raises(ValueError, match="approved catalogue"):
        generate_recommendations(fragrance(1, record_type=record_type), [fragrance(2)], [vector(1)])


def test_unapproved_catalogue_and_unsafe_vectors_are_rejected() -> None:
    with pytest.raises(ValueError, match="approved catalogue"):
        generate_recommendations(fragrance(1, approved=False), [], [vector(1)])
    with pytest.raises(ValueError, match="approved or review-safe"):
        generate_recommendations(fragrance(1), [fragrance(1)], [vector(1, status="rejected")])


def test_review_safe_vectors_default_to_human_review() -> None:
    results = generate_recommendations(
        fragrance(1),
        [fragrance(1), fragrance(2)],
        [vector(1, status="needs_human_review"), vector(2)],
    )
    assert results[0].review_status == "needs_human_review"


def test_contextual_filters_respect_all_available_fields() -> None:
    catalogue = [fragrance(1), fragrance(2, mood="bold"), fragrance(3, season="winter")]
    results = contextual_recommendations(
        catalogue,
        [vector(1), vector(2), vector(3)],
        mood="calm",
        occasion="day",
        season="spring",
        family="woody",
        intensity=0.5,
    )
    assert [item["fragrance_id"] for item in results] == [1]


def test_reasons_are_original_and_output_is_public_safe() -> None:
    restricted = "copied review wording"
    item = generate_recommendations(
        fragrance(1), [fragrance(1), fragrance(2)], [vector(1), vector(2)]
    )[0]
    output = public_recommendation(item)
    assert restricted not in item.reason
    assert set(output) == set(PUBLIC_RECOMMENDATION_FIELDS)
    assert PRIVATE_SUPPLIER_FIELDS.isdisjoint(output)


@pytest.mark.parametrize(
    "field", ["supplier_price", "supplier_code", "stock", "quantity", "cn_code", "commercial_terms"]
)
def test_supplier_private_input_is_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="Supplier-private"):
        generate_recommendations(fragrance(1, **{field: "private"}), [], [vector(1)])


def test_approval_guards_confidence_private_and_restricted_content() -> None:
    item = generate_recommendations(
        fragrance(1), [fragrance(1), fragrance(2)], [vector(1), vector(2)]
    )[0]
    with pytest.raises(ValueError, match="confidence"):
        approve_recommendation(replace(item, confidence_score=0.69))
    with pytest.raises(ValueError, match="Supplier-private"):
        approve_recommendation(replace(item, private_fields_detected=True))
    with pytest.raises(ValueError, match="Restricted"):
        approve_recommendation(replace(item, restricted_content_detected=True))


def test_csv_headers_and_batch_report(tmp_path: Path) -> None:
    with Path("data/recommendations.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert tuple(reader.fieldnames or ()) == OUTPUT_FIELDS
        assert list(reader)
    assert PRIVATE_SUPPLIER_FIELDS.isdisjoint(OUTPUT_FIELDS)

    catalogue_path = tmp_path / "catalogue.csv"
    vectors_path = tmp_path / "vectors.csv"
    output = tmp_path / "recommendations.csv"
    rows = [fragrance(1), fragrance(2)]
    with catalogue_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    vector_rows = []
    for item in [vector(1), vector(2)]:
        vector_rows.append(
            {
                "id": item.id,
                "fragrance_id": item.fragrance_id,
                **item.values,
                "confidence_score": item.confidence_score,
                "generation_method": item.generation_method,
                "review_status": item.review_status,
                "provenance_references": "1",
                "source_fingerprint": item.source_fingerprint,
                "rejection_reason": "",
            }
        )
    with vectors_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=vector_rows[0])
        writer.writeheader()
        writer.writerows(vector_rows)
    assert build_recommendations(catalogue_path, vectors_path, output) == (2, 0)
