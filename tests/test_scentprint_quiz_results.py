from aromatwin.services.scentprint_quiz_results import build_quiz_result
from aromatwin.services.scentprint_quiz_scoring import score_quiz_responses
from scripts.build_scentprint_quiz_samples import SAMPLE_RESPONSES


def test_demo_result_uses_alias_and_safe_fictional_match():
    result = build_quiz_result(score_quiz_responses("quiz_demo001", SAMPLE_RESPONSES), demo_mode=True)
    assert result["scentprint_public_alias"] == "quiz_demo001"
    assert "consumer" not in result
    match = result["recommended_product_matches"][0]
    assert match["product_title"] == "Fictional Horizon"
    assert "selected scent" in match["public_safe_explanation"]
    forbidden = {"supplier_price", "supplier_code", "cn_code", "stock", "quantity", "cost",
                 "margin", "seller_private_notes", "email", "phone", "raw_feedback"}
    assert not forbidden & set(match)


def test_unapproved_products_are_not_returned():
    scored = score_quiz_responses("quiz_demo001", SAMPLE_RESPONSES)
    result = build_quiz_result(scored, approved_products=[{
        "product_id": "hidden", "product_title": "Hidden", "public_safe": False,
        "review_status": "approved"}])
    assert result["recommended_product_matches"] == []
