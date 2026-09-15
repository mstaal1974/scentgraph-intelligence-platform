from fastapi.testclient import TestClient
from scentgraph.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "scentgraph", "version": "0.1.0"}


def test_openapi_exposes_required_routes() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert {
        "/brands",
        "/brands/{brand_id}",
        "/fragrances",
        "/fragrances/{fragrance_id}",
        "/notes",
        "/accords",
        "/search",
        "/similar/{fragrance_id}",
        "/recommend",
        "/scentprint",
        "/clone-matches/{fragrance_id}",
    } <= set(paths)
