"""Deterministic, explainable launch-readiness scoring using safe bands only."""

from typing import Any

BAND_SCORES = {"unknown": 0, "none": 0, "low": 25, "moderate": 55, "high": 80,
               "strong": 85, "excellent": 100, "ready": 100, "priority": 100}
WEIGHTS = {
    "profile_completeness_score": 0.14, "enrichment_confidence_score": 0.08,
    "supplier_availability_score": 0.13, "source_confidence_score": 0.11,
    "product_format_readiness_score": 0.13, "margin_suitability_score": 0.10,
    "seller_demand_score": 0.08, "consumer_interest_score": 0.08,
    "recommendation_readiness_score": 0.08, "bundle_potential_score": 0.07,
}


def _band(value: Any) -> int:
    if isinstance(value, bool):
        return 100 if value else 0
    return BAND_SCORES.get(str(value or "unknown").casefold(), 0)


def score_launch_readiness(candidate: dict[str, Any]) -> dict[str, Any]:
    """Score a candidate without inference; absent signals lower readiness."""
    dimensions = {
        "profile_completeness_score": 100 if candidate.get("profile_status") == "approved" else
        (55 if candidate.get("profile_status") in {"draft", "review"} else 0),
        "enrichment_confidence_score": _band(candidate.get("enrichment_status")),
        "supplier_availability_score": _band(candidate.get("supplier_availability_band")),
        "source_confidence_score": _band(candidate.get("source_confidence_band")),
        "product_format_readiness_score": _band(candidate.get("format_readiness")),
        "margin_suitability_score": _band(candidate.get("margin_suitability_band")),
        "seller_demand_score": _band(candidate.get("seller_demand_band")),
        "consumer_interest_score": _band(candidate.get("consumer_interest_band")),
        "recommendation_readiness_score": _band(candidate.get("recommendation_readiness")),
        "bundle_potential_score": _band(candidate.get("bundle_potential_band")),
    }
    missing = sum(candidate.get(key) in (None, "", "unknown", []) for key in (
        "profile_status", "supplier_availability_band", "source_confidence_band",
        "margin_suitability_band", "seller_demand_band", "consumer_interest_band"))
    penalties = {
        "privacy_risk_penalty": 40 if candidate.get("private_data_risk") else 0,
        "provenance_risk_penalty": 35 if candidate.get("provenance_risk") else 0,
        "missing_data_penalty": min(30, missing * 5),
    }
    gross = sum(dimensions[name] * weight for name, weight in WEIGHTS.items())
    score = round(max(0, min(100, gross - sum(penalties.values()))), 1)
    band = "priority" if score >= 80 else "strong" if score >= 65 else "moderate" if score >= 40 else "low"
    explanations = [f"{name.removesuffix('_score').replace('_', ' ')} contributed {value}/100"
                    for name, value in dimensions.items()]
    explanations += [f"{name.removesuffix('_penalty').replace('_', ' ')} deducted {value}"
                     for name, value in penalties.items() if value]
    return {**dimensions, **penalties, "launch_priority_score": score,
            "launch_priority_band": band, "explanations": explanations}
