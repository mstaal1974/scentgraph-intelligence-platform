from fastapi.testclient import TestClient

from aromatwin.config import Settings
from aromatwin.main import create_app
from aromatwin.schemas.seller_demand import SellerDemandBriefCreate
from aromatwin.services.seller_demand_briefs import create_brief
from aromatwin.services.seller_supplier_matching import match_brief_to_candidates, public_safe_match

FORBIDDEN = ("price", "cost", "supplier_code", "cn_code", "quantity", "stock", "aed", "usd")


def test_explainable_match_uses_requested_dimensions_and_stays_safe() -> None:
    brief = create_brief(SellerDemandBriefCreate(
        seller_name="Private", seller_segment="niche", target_customer="adult",
        desired_fragrance_families=["woody"], desired_notes=["cedar"],
        desired_accords=["dry woods"], desired_moods=["calm"], desired_occasions=["work"],
        desired_seasons=["autumn"], product_formats=["30ml bottle"], target_margin_band="strong"))
    candidate = {"supplier_name": "Secret supplier", "supplier_offer_id": "private-1",
        "canonical_fragrance_name": "Fictional Cedar", "fragrance_families": ["woody"],
        "notes": ["cedar"], "accords": ["dry woods"], "moods": ["calm"],
        "occasions": ["work"], "seasons": ["autumn"], "product_formats": ["30ml bottle"],
        "profile_completeness": .9, "catalogue_readiness": .8, "source_confidence": .9,
        "reference": "internal-reference", "margin_suitability_band": "strong",
        "supplier_price": 10, "supplier_code": "SECRET"}
    match = match_brief_to_candidates(brief, [candidate])[0]
    public = public_safe_match(match)
    assert match.overall_match_score > .8
    assert match.review_status == "needs_human_review"
    assert any("mood fit" in reason for reason in match.match_reasons)
    assert not any(token in key.casefold() for key in public for token in FORBIDDEN)
    assert "supplier_offer_id" not in public
    assert "sku" not in public and "catalogue_record" not in public


def test_missing_reference_lowers_readiness() -> None:
    brief = create_brief(SellerDemandBriefCreate(seller_name="P", seller_segment="niche",
        target_customer="adult", product_formats=["50ml bottle"]))
    base = {"supplier_name": "S", "canonical_fragrance_name": "Candidate",
            "product_formats": ["50ml bottle"], "profile_completeness": .9,
            "catalogue_readiness": .9, "source_confidence": .9}
    with_reference = match_brief_to_candidates(brief, [{**base, "reference": "ORI"}])[0]
    without = match_brief_to_candidates(brief, [base])[0]
    assert without.launch_readiness_score < with_reference.launch_readiness_score
    assert "missing_reference" in without.risk_flags


def test_openapi_exposes_internal_routes_with_safe_schemas() -> None:
    schema = TestClient(create_app(Settings(environment="test"))).get("/openapi.json").json()
    assert "/seller-demand/briefs" in schema["paths"]
    properties = schema["components"]["schemas"]["SellerDemandBriefRead"]["properties"]
    assert "private_seller_notes" not in properties and "seller_name" not in properties
