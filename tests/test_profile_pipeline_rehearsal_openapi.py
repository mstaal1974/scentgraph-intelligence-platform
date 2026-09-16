from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_internal_rehearsal_routes():
    app = create_app(Settings(enable_private_supplier_endpoints=True))
    paths = app.openapi()["paths"]
    expected = [
        "/profile-pipeline-rehearsal/health",
        "/profile-pipeline-rehearsal/run",
        "/profile-pipeline-rehearsal/{rehearsal_id}",
        "/profile-pipeline-rehearsal/{rehearsal_id}/trace",
        "/profile-pipeline-rehearsal/{rehearsal_id}/gaps",
        "/profile-pipeline-rehearsal/gap-report/build",
        "/profile-pipeline-rehearsal/audit",
    ]
    assert all(any(path.endswith(item) for path in paths) for item in expected)
