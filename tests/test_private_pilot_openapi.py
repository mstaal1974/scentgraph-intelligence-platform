from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_private_pilot_routes():
    app = create_app(Settings(enable_private_supplier_endpoints=True))
    paths = app.openapi()["paths"]
    expected = {"/private-pilot/health", "/private-pilot/intake/scan", "/private-pilot/intake",
        "/private-pilot/execution-plan/build", "/private-pilot/execution-plan/{run_id}",
        "/private-pilot/run", "/private-pilot/runs/{run_id}/acceptance",
        "/private-pilot/runs/{run_id}/acceptance/export", "/private-pilot/audit"}
    prefix = app.state.settings.internal_api_prefix
    assert {prefix + path for path in expected} <= set(paths)
