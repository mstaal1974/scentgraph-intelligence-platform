from aromatwin.services.launch_readiness_scoring import score_launch_readiness


def test_scoring_is_deterministic_explainable_and_missing_lowers_score():
    ready = {"profile_status": "approved", "enrichment_status": "high", "supplier_availability_band": "high",
             "source_confidence_band": "high", "format_readiness": "ready", "margin_suitability_band": "strong",
             "seller_demand_band": "strong", "consumer_interest_band": "high",
             "recommendation_readiness": "ready", "bundle_potential_band": "high"}
    assert score_launch_readiness(ready) == score_launch_readiness(ready)
    result = score_launch_readiness(ready)
    assert result["launch_priority_score"] > score_launch_readiness({})["launch_priority_score"]
    assert len(result["explanations"]) == 10
