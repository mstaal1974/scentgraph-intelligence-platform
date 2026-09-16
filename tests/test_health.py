from fastapi.testclient import TestClient


def test_app_imports(app: object) -> None:
    assert app is not None


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "aromatwin", "version": "0.2.0"}


def test_openapi_exposes_workflow_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    required = {
        "/supplier-items",
        "/supplier-items/{item_id}",
        "/supplier-items/import-preview",
        "/match-candidates",
        "/match-candidates/{candidate_id}",
        "/match-candidates/generate",
        "/enrichment-reviews",
        "/enrichment-reviews/{enrichment_review_id}",
        "/enrichment-reviews/{enrichment_review_id}/approve",
        "/enrichment-reviews/{enrichment_review_id}/reject",
        "/brands",
        "/fragrances",
        "/notes",
        "/accords",
        "/search",
        "/similar/{fragrance_id}",
        "/recommendations",
        "/scentprint",
        "/clone-matches/{fragrance_id}",
        "/scent-vectors",
        "/scent-vectors/generate",
        "/scent-vectors/similarity",
    }
    assert required.issubset(paths)


def test_import_preview_remains_unapproved_staging(client: TestClient) -> None:
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
