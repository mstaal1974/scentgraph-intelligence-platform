from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_platform_completion_endpoints():
    paths = create_app(Settings(enable_private_supplier_endpoints=True)).openapi()["paths"]
    expected = {"/platform-completion/health", "/platform-completion/tasks",
                "/platform-completion/run-safe-checks", "/platform-completion/run-demo-completion",
                "/platform-completion/readiness", "/platform-completion/blockers",
                "/platform-completion/readiness/export", "/platform-completion/audit"}
    assert expected <= set(paths)
