import csv
from dataclasses import replace
from pathlib import Path

import pytest

from aromatwin.services.catalogue_promotion import PRIVATE_SUPPLIER_FIELDS
from aromatwin.services.scent_vector_engine import (
    VECTOR_DIMENSIONS,
    approve_scent_vector,
    generate_scent_vector,
    similarity,
)
from scripts.build_scent_vectors import OUTPUT_FIELDS, build_vectors


def catalogue(**changes: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": 1,
        "record_type": "catalogue_fragrance",
        "approved": True,
        "family": "woody aromatic",
        "notes": "cedar bergamot moss",
        "accords": "fresh green woody",
        "season": "spring",
        "occasion": "day",
        "mood": "refined",
        "description_original": "An original bright forest composition.",
        "concentration": "eau de parfum",
        "provenance_references": (11,),
    }
    record.update(changes)
    return record


def test_approved_catalogue_generates_bounded_complete_vector() -> None:
    vector = generate_scent_vector(catalogue())
    assert set(vector.values) == set(VECTOR_DIMENSIONS)
    assert all(0 <= value <= 1 for value in vector.values.values())
    assert vector.provenance_references == (11,)


@pytest.mark.parametrize("record_type", ["supplier_item", "profile_draft", "enrichment_review"])
def test_non_catalogue_layers_cannot_generate_public_vector(record_type: str) -> None:
    with pytest.raises(ValueError, match="Only catalogue"):
        generate_scent_vector(catalogue(record_type=record_type))


def test_unapproved_catalogue_is_rejected() -> None:
    with pytest.raises(ValueError, match="approved"):
        generate_scent_vector(catalogue(approved=False))


@pytest.mark.parametrize(
    "field", ["supplier_price", "supplier_code", "stock", "quantity", "cn_code", "commercial_terms"]
)
def test_supplier_private_input_is_excluded(field: str) -> None:
    with pytest.raises(ValueError, match="Supplier-private"):
        generate_scent_vector(catalogue(**{field: "private"}))


def test_approval_guards_confidence_and_restricted_content() -> None:
    vector = generate_scent_vector(catalogue(notes=""))
    with pytest.raises(ValueError, match="confidence"):
        approve_scent_vector(replace(vector, confidence_score=0.69))
    with pytest.raises(ValueError, match="Restricted"):
        approve_scent_vector(replace(vector, restricted_content_detected=True, confidence_score=0.9))


def test_similarity_ordering_and_duplicate_generation() -> None:
    source = generate_scent_vector(catalogue())
    duplicate = generate_scent_vector(catalogue(), [source])
    similar = generate_scent_vector(catalogue(id=2, notes="cedar moss"), [source])
    different = generate_scent_vector(
        catalogue(id=3, family="gourmand", notes="caramel chocolate vanilla", accords="sweet"),
        [source, similar],
    )
    assert duplicate is source
    assert similarity(source, similar) > similarity(source, different)


def test_csv_has_public_safe_headers_and_cli_report(tmp_path: Path) -> None:
    with Path("data/scent_vectors.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert tuple(reader.fieldnames or ()) == OUTPUT_FIELDS
        assert list(reader)
    assert PRIVATE_SUPPLIER_FIELDS.isdisjoint(OUTPUT_FIELDS)

    source = tmp_path / "catalogue.csv"
    output = tmp_path / "vectors.csv"
    row = catalogue()
    with source.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=row)
        writer.writeheader()
        writer.writerow(row)
    assert build_vectors(source, output) == (1, 0)
