"""Build non-executing launch plans from public-safe candidate projections."""

from typing import Any
from uuid import NAMESPACE_URL, uuid5


def build_launch_plans(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    themes = {
        "top_50_launch_candidates": lambda c: c.get("launch_priority_band") in {"priority", "strong"},
        "sample_first_launch": lambda c: "10ml" in c.get("recommended_product_formats", []),
        "bundle_candidates": lambda c: c.get("bundle_potential_band") in {"high", "strong"},
        "car_diffuser_launch": lambda c: "car diffuser" in c.get("recommended_product_formats", []),
        "body_care_layering_launch": lambda c: "body care" in c.get("recommended_product_formats", []),
        "profile_enrichment_needed": lambda c: c.get("launch_status") == "launch_after_profile_enrichment",
        "supplier_review_needed": lambda c: c.get("launch_status") == "launch_after_supplier_review",
        "catalogue_approval_needed": lambda c: c.get("launch_status") == "launch_after_catalogue_approval",
        "product_setup_needed": lambda c: c.get("launch_status") == "launch_after_product_setup",
        "recommendation_setup_needed": lambda c: "missing_recommendations" in c.get("missing_requirements", []),
        "high_margin_priority": lambda c: c.get("margin_suitability_band") in {"high", "strong"},
        "seller_demand_priority": lambda c: c.get("seller_demand_band") in {"high", "strong"},
        "consumer_interest_priority": lambda c: c.get("consumer_interest_band") in {"high", "strong"},
    }
    plans = []
    ordered = sorted(candidates, key=lambda c: -float(c.get("launch_priority_score", 0)))
    for theme, predicate in themes.items():
        selected = [item for item in ordered if predicate(item)][:50]
        if not selected:
            continue
        ids = [str(item["launch_candidate_id"]) for item in selected]
        formats = sorted({fmt for item in selected for fmt in item.get("recommended_product_formats", [])})
        plans.append({"plan_id": str(uuid5(NAMESPACE_URL, f"launch-plan:{theme}:{','.join(ids)}")),
                      "plan_theme": theme, "candidate_count": len(selected),
                      "recommended_candidates": ids, "recommended_formats": formats,
                      "rationale": "Candidates meet the plan's aggregated, public-safe criteria.",
                      "blocking_issues": sorted({issue for item in selected for issue in item.get("blocking_issues", [])}),
                      "next_actions": sorted({item.get("recommended_next_action", "Human review required") for item in selected}),
                      "review_status": "needs_human_review"})
    return plans
