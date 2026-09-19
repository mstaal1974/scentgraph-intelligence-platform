"""The first-party profile library and the intelligence derived from it."""

import csv
from pathlib import Path

import pytest

from aromatwin.library import HOUSES, build_seed_profiles
from aromatwin.schemas.maison import MaisonScentprintRequest
from aromatwin.services.catalogue_promotion import TAXONOMY_FIELDS
from aromatwin.services.maison_integration import (
    PRIVATE_FIELDS,
    RESTRICTED_FIELDS,
    MaisonIntegrationService,
)
from aromatwin.services.scent_vector_engine import PUBLIC_SOURCE_FIELDS, VECTOR_DIMENSIONS

DATA = Path("data")


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


@pytest.fixture(scope="module")
def catalogue() -> list[dict[str, str]]:
    return rows("catalogue_fragrances.csv")


def test_seed_profiles_are_unique_and_evenly_distributed() -> None:
    profiles = build_seed_profiles()
    assert len(profiles) == len(HOUSES) * 4
    assert len({(item.house, item.name) for item in profiles}) == len(profiles)
    per_direction = {item.direction.key for item in profiles}
    counts = [sum(1 for item in profiles if item.direction.key == key) for key in per_direction]
    assert len(set(counts)) == 1, "each direction should carry the same number of profiles"


def test_catalogue_carries_the_taxonomy_the_vector_engine_reads(catalogue) -> None:
    """The schema gap that previously produced all-zero vectors must stay closed."""
    assert catalogue
    for field in TAXONOMY_FIELDS:
        assert field in catalogue[0], field
        assert all(row[field].strip() for row in catalogue), field
    structured = set(PUBLIC_SOURCE_FIELDS) & set(TAXONOMY_FIELDS)
    assert structured, "vector generation must read the catalogue taxonomy"


def test_every_catalogue_record_has_a_discriminative_vector(catalogue) -> None:
    vectors = {int(row["fragrance_id"]): row for row in rows("scent_vectors.csv")}
    assert set(vectors) == {int(row["id"]) for row in catalogue}
    for fragrance_id, vector in vectors.items():
        values = [float(vector[name]) for name in VECTOR_DIMENSIONS]
        assert any(values), f"fragrance {fragrance_id} has an all-zero vector"
        assert all(0 <= value <= 1 for value in values)
    signatures = {tuple(vector[name] for name in VECTOR_DIMENSIONS) for vector in vectors.values()}
    assert len(signatures) > len(vectors) * 0.8, "vectors are not discriminative enough"


def test_library_carries_no_private_or_restricted_columns(catalogue) -> None:
    forbidden = PRIVATE_FIELDS | RESTRICTED_FIELDS
    for name in ("catalogue_fragrances.csv", "scent_vectors.csv", "recommendations.csv",
                 "clone_relationships.csv"):
        assert forbidden.isdisjoint(rows(name)[0]), name


def test_maison_serves_the_library_with_vectors_and_relationships() -> None:
    service = MaisonIntegrationService()
    cards = service.list_fragrances()
    assert len(cards) >= 40
    detail = service.detail(cards[0].id)
    assert detail is not None
    assert detail.notes and detail.scent_vector is not None
    assert any(value > 0 for value in detail.scent_vector.dimensions.values())
    assert service.recommendations_for(cards[0].id)


def test_scentprint_ranks_by_strength_not_only_direction() -> None:
    """Regression: scoring the requested dimensions alone normalised magnitude away.

    A profile with woody 0.1 then tied with one at woody 1.0, and a profile whose strength lay
    in dimensions the caller never asked for was not penalised for them.
    """
    catalogue = [
        {"id": 1, "brand": "B", "name": "Strong", "slug": "strong", "review_status": "approved",
         "provenance_references": "1"},
        {"id": 2, "brand": "B", "name": "Faint", "slug": "faint", "review_status": "approved",
         "provenance_references": "1"},
        {"id": 3, "brand": "B", "name": "Elsewhere", "slug": "elsewhere",
         "review_status": "approved", "provenance_references": "1"},
    ]
    vectors = [
        {"fragrance_id": 1, "review_status": "approved", "confidence_score": "0.9", "woody": "1.0"},
        {"fragrance_id": 2, "review_status": "approved", "confidence_score": "0.9", "woody": "0.1"},
        {"fragrance_id": 3, "review_status": "approved", "confidence_score": "0.9", "woody": "0.2",
         "floral": "1.0", "sweet": "1.0"},
    ]
    service = MaisonIntegrationService(
        catalogue=catalogue, vectors=vectors, recommendations=[], relationships=[]
    )
    results = service.scentprint(MaisonScentprintRequest(dimensions={"woody": 1.0}, limit=3))
    assert [item.fragrance.id for item in results] == [1, 2, 3]
    assert results[0].score > results[1].score > results[2].score
