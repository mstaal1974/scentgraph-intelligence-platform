from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_private_review_workflow():
    app = create_app(Settings(enable_private_supplier_endpoints=True))
    paths = app.openapi()["paths"]
    expected = {"/review-workflow/health", "/review-workflow/queues/build",
                "/review-workflow/queues", "/review-workflow/queues/{review_item_id}",
                "/review-workflow/gates", "/review-workflow/gates/{gate_id}",
                "/review-workflow/decisions", "/review-workflow/readiness",
                "/review-workflow/audit"}
    assert all(any(path.endswith(endpoint) for path in paths) for endpoint in expected)
