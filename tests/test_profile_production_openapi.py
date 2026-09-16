from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_profile_production_endpoints():
    paths = create_app(Settings(enable_private_supplier_endpoints=True)).openapi()["paths"]
    expected = {
        "/profile-production/health", "/profile-production/readiness",
        "/profile-production/readiness/check", "/profile-production/batch-plan/build",
        "/profile-production/batch-plan/{batch_plan_id}", "/profile-production/run",
        "/profile-production/runs/{run_id}", "/profile-production/runs/{run_id}/drafts",
        "/profile-production/review-packet/build",
        "/profile-production/review-packets/{review_packet_id}", "/profile-production/audit",
    }
    assert expected <= set(paths)
