from fastapi.testclient import TestClient

from aromatwin.config import Settings
from aromatwin.main import create_app
from aromatwin.services.launch_intelligence import build_launch_candidate, public_summary


def candidate(**changes):
    value = {"fragrance_id": "f1", "product_id": "p1", "canonical_brand": "Fictional Atelier",
             "canonical_fragrance_name": "Fictional Scent", "product_title": "Discovery Size",
             "profile_status": "approved", "enrichment_status": "high", "catalogue_status": "approved",
             "product_status": "ready", "supplier_availability_band": "high", "source_confidence_band": "high",
             "margin_suitability_band": "strong", "seller_demand_band": "strong",
             "consumer_interest_band": "high", "recommendation_readiness": "ready",
             "bundle_potential_band": "moderate", "format_readiness": "ready",
             "scent_vector_status": "approved", "recommended_product_formats": ["10ml", "50ml"]}
    value.update(changes)
    return value


def test_combines_signals_without_auto_approval_or_mutation():
    source = candidate()
    record = build_launch_candidate(source)
    assert record["launch_priority_band"] in {"strong", "priority"}
    assert record["launch_status"] == "launch_now"
    assert record["review_status"] == "needs_human_review"
    assert source == candidate()  # no catalogue, SKU, or campaign mutation


def test_risk_holds_take_precedence():
    assert build_launch_candidate(candidate(source_confidence_band="low"))["launch_status"] == "hold_low_confidence"
    assert build_launch_candidate(candidate(provenance_risk=True))["launch_status"] == "hold_missing_provenance"
    assert build_launch_candidate(candidate(private_data_risk=True))["launch_status"] == "hold_private_data_risk"


def test_public_projection_is_allow_listed():
    record = build_launch_candidate(candidate()) | {"supplier_price": 1, "supplier_code": "secret",
        "cn_code": "secret", "stock": 5, "quantity": 2, "aed_price": 1, "usd_price": 1,
        "supplier_cost": 1, "raw_margin": 1, "commercial_terms": "secret",
        "seller_private_notes": "secret", "consumer_private_data": "secret"}
    output = public_summary(record)
    assert not set(record) - set(output) <= set(output)
    assert all(key not in output for key in set(record) - set(output))


def test_openapi_exposes_launch_routes():
    app = create_app(Settings(environment="test", private_api_key="test"))
    paths = app.openapi()["paths"]
    for path in ("/launch-intelligence/health", "/launch-intelligence/build",
                 "/launch-intelligence/candidates", "/launch-intelligence/priority/top",
                 "/launch-intelligence/gaps", "/launch-intelligence/plans/build",
                 "/launch-intelligence/audit"):
        assert path in paths
    assert TestClient(app).get("/launch-intelligence/health", headers={"X-Private-API-Key": "test"}).status_code == 200
