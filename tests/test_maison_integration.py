import csv
import json
from pathlib import Path

from aromatwin.main import app
from aromatwin.routers import maison
from aromatwin.schemas.maison import MaisonScentprintRequest
from aromatwin.services.maison_integration import (
    PRIVATE_FIELDS,
    RESTRICTED_FIELDS,
    MaisonIntegrationService,
)
from scripts.export_maison_catalogue import CATALOGUE_FIELDS, RECOMMENDATION_FIELDS, export


def record(identifier: int, **changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": identifier,
        "record_type": "catalogue_fragrance",
        "approved": True,
        "slug": f"scent-{identifier}",
        "name": f"Scent {identifier}",
        "brand": "Fiction House",
        "family": "woody",
        "notes": "cedar,bergamot",
        "accords": "woody,fresh",
        "mood": "calm",
        "occasion": "day",
        "season": "spring",
        "source_confidence": 0.9,
        "provenance_references": "1",
        "review_status": "approved",
    }
    row.update(changes)
    return row


def vector(identifier: int, woody: float) -> dict[str, object]:
    return {
        "id": identifier,
        "fragrance_id": identifier,
        "woody": woody,
        "fresh": 1 - woody,
        "confidence_score": 0.9,
        "review_status": "approved",
    }


def service() -> MaisonIntegrationService:
    catalogue = [
        record(1),
        record(2),
        record(3, approved=False),
        record(4, record_type="supplier_item"),
        record(5, record_type="profile_draft"),
        record(6, record_type="enrichment_review"),
    ]
    recommendations = [
        {
            "source_fragrance_id": 1,
            "recommended_fragrance_id": 2,
            "recommendation_type": "similar_fragrance",
            "score": 0.88,
            "confidence_score": 0.85,
            "reason": "Shared public woody profile.",
            "review_status": "approved",
        },
        {
            "source_fragrance_id": 1,
            "recommended_fragrance_id": 3,
            "score": 1,
            "review_status": "approved",
        },
    ]
    return MaisonIntegrationService(
        catalogue, [vector(1, 0.8), vector(2, 0.7), vector(3, 0.8)], recommendations
    )


def flatten(value: object) -> str:
    return json.dumps(value, default=str).lower()


def test_only_approved_catalogue_and_workflow_records_never_appear() -> None:
    result = service().list_fragrances()
    assert [item.id for item in result] == [1, 2]
    assert all(
        word not in flatten(result)
        for word in ("supplier_item", "profile_draft", "enrichment_review")
    )


def test_detail_and_slug_are_allowlisted() -> None:
    integration = service()
    detail = integration.detail(1)
    assert detail and integration.by_slug("scent-1") == detail
    output = detail.model_dump()
    assert PRIVATE_FIELDS.isdisjoint(output)
    assert RESTRICTED_FIELDS.isdisjoint(output)


def test_similar_recommendations_and_scentprint_are_ranked_and_safe() -> None:
    integration = service()
    similar = integration.similar(1)
    recommendations = integration.recommendations_for(1)
    matches = integration.scentprint(MaisonScentprintRequest(dimensions={"woody": 1}, limit=2))
    assert similar and similar[0].rank == 1 and similar[0].fragrance.id == 2
    assert recommendations and recommendations[0].review_status == "approved"
    assert [item.rank for item in matches] == [1, 2]
    assert all(PRIVATE_FIELDS.isdisjoint(item.model_dump()) for item in matches)


def test_unsafe_source_rows_and_unapproved_intelligence_are_excluded() -> None:
    unsafe = [record(7, supplier_price="10"), record(8, third_party_description="copied")]
    integration = MaisonIntegrationService(
        [record(1), record(2), *unsafe],
        [vector(1, 0.8), {**vector(2, 0.7), "review_status": "needs_human_review"}],
        [
            {
                "source_fragrance_id": 1,
                "recommended_fragrance_id": 2,
                "score": 1,
                "confidence_score": 1,
                "reason": "x",
                "review_status": "needs_human_review",
            }
        ],
    )
    assert [item.id for item in integration.list_fragrances()] == [1, 2]
    assert integration.detail(2).scent_vector is None  # type: ignore[union-attr]
    assert integration.recommendations_for(1) == []


def test_api_and_openapi(monkeypatch) -> None:
    monkeypatch.setattr(maison, "SERVICE", service())
    assert [item.id for item in maison.fragrances()] == [1, 2]
    assert maison.fragrance_by_slug("scent-1").id == 1
    assert maison.similar(1)[0].rank == 1
    assert maison.recommendations(1)[0].fragrance.id == 2
    assert maison.scentprint_match(MaisonScentprintRequest(dimensions={"woody": 1}))
    paths = app.openapi()["paths"]
    expected = {
        "/maison/health",
        "/maison/fragrances",
        "/maison/fragrances/{fragrance_id}",
        "/maison/fragrances/slug/{slug}",
        "/maison/fragrances/{fragrance_id}/similar",
        "/maison/fragrances/{fragrance_id}/recommendations",
        "/maison/scentprint/match",
        "/maison/export/catalogue",
        "/maison/export/recommendations",
    }
    assert expected <= paths.keys()
    payload = flatten(maison.fragrance(1).model_dump())
    for forbidden in PRIVATE_FIELDS | RESTRICTED_FIELDS:
        assert f'"{forbidden}"' not in payload


def test_export_headers_and_report(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    rows = [record(1), record(2, approved=False)]
    with (data / "catalogue_fragrances.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    for name, rows_to_write in (
        ("scent_vectors.csv", [vector(1, 0.8)]),
        ("recommendations.csv", []),
    ):
        with (data / name).open("w", newline="", encoding="utf-8") as stream:
            if rows_to_write:
                writer = csv.DictWriter(stream, fieldnames=rows_to_write[0])
                writer.writeheader()
                writer.writerows(rows_to_write)
            else:
                stream.write("source_fragrance_id,recommended_fragrance_id,review_status\n")
    catalogue, recommendations = tmp_path / "catalogue.csv", tmp_path / "recommendations.csv"
    assert export(data, catalogue, recommendations) == (1, 1)
    with catalogue.open(newline="", encoding="utf-8") as stream:
        assert tuple(csv.DictReader(stream).fieldnames or ()) == CATALOGUE_FIELDS
    with recommendations.open(newline="", encoding="utf-8") as stream:
        assert tuple(csv.DictReader(stream).fieldnames or ()) == RECOMMENDATION_FIELDS
    assert PRIVATE_FIELDS.isdisjoint(set(CATALOGUE_FIELDS) | set(RECOMMENDATION_FIELDS))
    assert RESTRICTED_FIELDS.isdisjoint(set(CATALOGUE_FIELDS) | set(RECOMMENDATION_FIELDS))
