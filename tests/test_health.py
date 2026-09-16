from fastapi.testclient import TestClient
from aromatwin.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "aromatwin", "version": "0.2.0"}


def test_openapi_exposes_workflow_routes() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    required = {
        "/supplier-items",
        "/supplier-items/{item_id}",
        "/supplier-items/import-preview",
        "/match-candidates",
        "/match-candidates/{candidate_id}",
        "/match-candidates/generate",
        "/enrichment-reviews",
        "/enrichment-reviews/{review_id}",
        "/enrichment-reviews/{review_id}/approve",
        "/enrichment-reviews/{review_id}/reject",
        "/brands",
        "/fragrances",
        "/notes",
        "/accords",
        "/search",
        "/similar/{fragrance_id}",
        "/recommend",
        "/scentprint",
        "/clone-matches/{fragrance_id}",
    }
    assert required <= set(paths)


def test_import_preview_remains_unapproved_staging() -> None:
    response = client.post(
        "/supplier-items/import-preview",
        json={
            "supplier_name": "Supplier A",
            "source_file": "supplier.csv",
            "rows": [
                {
                    "BRAND": "Oil House",
                    "NAME": "Example SUPER",
                    "ORI": "Original Brand / Original Scent",
                    "CN CODE": "CN-1",
                    "QTY": 5,
                    "AED": 100,
                    "USD": 27.23,
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "supplier_imported"
    assert payload["catalogue_promotion_allowed"] is False
    assert payload["rows"][0]["status"] == "supplier_imported"
    assert payload["rows"][0]["variant_marker"] == "SUPER"
