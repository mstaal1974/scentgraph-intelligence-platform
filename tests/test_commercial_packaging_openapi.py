from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_commercial_packaging_endpoints():
    paths = create_app(Settings()).openapi()["paths"]
    expected = {"/commercial-packaging/health", "/commercial-packaging/plans",
                "/commercial-packaging/plans/{plan_id}", "/commercial-packaging/entitlements",
                "/commercial-packaging/entitlements/{plan_id}",
                "/commercial-packaging/entitlements/check",
                "/commercial-packaging/tenant-feature-access",
                "/commercial-packaging/tenant-feature-access/check",
                "/commercial-packaging/readiness", "/commercial-packaging/readiness/check",
                "/commercial-packaging/audit"}
    assert expected <= set(paths)
    assert "requestBody" in paths["/commercial-packaging/entitlements/check"]["post"]
