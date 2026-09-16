from aromatwin.services.launch_recommendation_planner import build_launch_plans


def test_planner_builds_requested_non_executing_format_plans():
    item = {"launch_candidate_id": "x", "launch_priority_band": "priority", "launch_priority_score": 90,
            "launch_status": "launch_now", "bundle_potential_band": "high",
            "recommended_product_formats": ["10ml", "car diffuser", "body care"],
            "margin_suitability_band": "high", "seller_demand_band": "strong", "consumer_interest_band": "high",
            "blocking_issues": [], "missing_requirements": [], "recommended_next_action": "Human review"}
    themes = {plan["plan_theme"] for plan in build_launch_plans([item])}
    assert {"top_50_launch_candidates", "sample_first_launch", "bundle_candidates",
            "car_diffuser_launch", "body_care_layering_launch"} <= themes
