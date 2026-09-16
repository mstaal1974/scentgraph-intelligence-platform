from aromatwin.config import Settings
from aromatwin.main import create_app


def _schema_references(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref":
                yield child.rsplit("/", 1)[-1]
            else:
                yield from _schema_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from _schema_references(child)


def _property_names(value):
    if isinstance(value, dict):
        properties = value.get("properties", {})
        yield from properties
        for child in value.values():
            yield from _property_names(child)
    elif isinstance(value, list):
        for child in value:
            yield from _property_names(child)


def test_openapi_exposes_internal_operations_endpoints():
    app = create_app(
        Settings(database_url="sqlite:///:memory:", enable_private_supplier_endpoints=True)
    )
    openapi = app.openapi()
    paths = openapi["paths"]
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
        "supplier_cost",
        "supplier_code",
        "cn_code",
        "stock",
        "quantity",
        "aed",
        "usd",
        "raw_margin",
        "margin",
        "commercial_terms",
        "seller_private_notes",
        "consumer_private_notes",
        "private_note",
        "free_text_private_note",
        "email",
        "phone",
        "address",
    }
    operation_specs = {path: paths[path] for path in expected}
    schemas = openapi["components"]["schemas"]
    pending = set(_schema_references(operation_specs))
    referenced = {}
    while pending:
        name = pending.pop()
        if name in referenced or name not in schemas:
            continue
        referenced[name] = schemas[name]
        pending.update(_schema_references(schemas[name]))

    operation_fields = {name.casefold() for name in _property_names(operation_specs)}
    operation_fields.update(name.casefold() for name in _property_names(referenced))
    assert forbidden.isdisjoint(operation_fields)
