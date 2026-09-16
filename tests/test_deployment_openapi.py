from aromatwin.main import create_app


def test_openapi_exposes_deployment_endpoints() -> None:
    paths = create_app().openapi()["paths"]
    assert {"/deployment/health", "/deployment/readiness", "/deployment/environment", "/deployment/readiness/check", "/deployment/audit"}.issubset(paths)
