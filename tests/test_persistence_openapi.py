from aromatwin.config import Settings
from aromatwin.main import create_app


def test_openapi_exposes_internal_operations_endpoints():
    app = create_app(
        Settings(database_url="sqlite:///:memory:", enable_private_supplier_endpoints=True)
    )
    paths = app.openapi()["paths"]
    expected = {
        "/operations/health",
        "/operations/runs",
        "/operations/runs/{run_id}",
        "/operations/runs/{run_id}/stages",
        "/operations/runs/{run_id}/artifacts",
        "/operations/review-items",
        "/operations/launch-candidates",
        "/operations/provenance",
        "/operations/audit-events",
        "/operations/audit",
        "/operations/audit/export",
    }
    assert expected <= paths.keys()
    forbidden = {
        "supplier_price",
        "supplier_code",
        "cn_code",
        "stock",
        "quantity",
        "aed",
        "usd",
        "seller_private_notes",
        "consumer_private_notes",
        "email",
        "phone",
    }
    schema_text = str(app.openapi()["components"]["schemas"]).casefold()
    assert not forbidden & set(schema_text.replace("'", "").replace(":", " ").split())
