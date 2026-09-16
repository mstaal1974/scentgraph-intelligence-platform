from fastapi.testclient import TestClient

from aromatwin.main import create_app
from aromatwin.services.product_catalogue import ProductCatalogueService


def record(**changes):
    row = {
        "id": 7,
        "brand": "Fiction House",
        "name": "Quiet Orbit",
        "review_status": "approved",
        "family": "woody",
        "mood": "calm",
    }
    row.update(changes)
    return row


def test_only_approved_safe_records_become_original_products():
    service = ProductCatalogueService(
        catalogue=[
            record(),
            record(id=8, review_status="rejected"),
            record(id=9, supplier_price="10"),
        ],
        vectors=[],
        recommendations=[],
    )
    products = service.build()
    assert len(products) == 1
    assert products[0]["public_description_original"].startswith("Meet Quiet Orbit")
    assert not (
        {
            "supplier_price",
            "supplier_cost",
            "margin",
            "supplier_code",
            "cn_code",
            "quantity",
            "stock",
            "aed",
            "usd",
            "commercial_terms",
        }
        & products[0].keys()
    )


def test_openapi_and_public_endpoint_are_safe():
    client = TestClient(create_app())
    schema = client.get("/openapi.json").json()
    assert "/products" in schema["paths"]
    response = client.get("/products")
    assert response.status_code == 200
    assert all("supplier_price" not in item for item in response.json())
