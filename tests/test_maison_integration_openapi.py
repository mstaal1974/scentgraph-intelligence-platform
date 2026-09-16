from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_internal_maison_routes():
    app = create_app(Settings(environment="local", enable_private_supplier_endpoints=True))
    paths = app.openapi()["paths"]
    expected = ["/health", "/readiness", "/readiness/check", "/contracts/products",
                "/contracts/recommendations", "/contracts/scentprint-matches", "/contracts/bundles",
                "/sync-manifest/build", "/sync-manifest/{sync_manifest_id}", "/audit"]
    assert all(f"/maison-integration{x}" in paths for x in expected)
