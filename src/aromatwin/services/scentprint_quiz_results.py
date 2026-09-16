"""Public-safe presentation payloads derived from Scentprint preference vectors."""

from typing import Any


def _top(weights: dict[str, float], limit: int = 3) -> list[str]:
    return [key for key, _ in sorted(weights.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _demo_matches(vector: dict[str, Any]) -> list[dict[str, object]]:
    families = _top(vector["scent_family_weights"], 2)
    accords = _top(vector["accord_weights"], 2)
    moods = _top(vector["mood_weights"], 2)
    return [{
        "product_id": "demo-product-001",
        "product_title": "Fictional Horizon",
        "product_format": "sample",
        "match_score_band": "strong" if families or accords else "exploratory",
        "match_reason": "Shares selected scent-preference categories.",
        "shared_families": families,
        "shared_accords": accords,
        "shared_moods": moods,
        "public_safe_explanation": (
            "This fictional demo match reflects only the selected scent families, accords, and moods."
        ),
    }]


def build_quiz_result(
    scored: dict[str, Any], *, demo_mode: bool = False,
    approved_products: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build a non-diagnostic result; only explicitly approved records may be supplied."""
    vector = scored["preference_vector"]
    families = _top(vector["scent_family_weights"])
    matches = _demo_matches(vector) if demo_mode and not approved_products else []
    if approved_products:
        for product in approved_products:
            if product.get("public_safe") is not True or product.get("review_status") != "approved":
                continue
            matches.append({
                "product_id": str(product["product_id"]),
                "product_title": str(product["product_title"]),
                "product_format": str(product.get("product_format", "unspecified")),
                "match_score_band": "moderate",
                "match_reason": "Uses approved scent-preference metadata.",
                "shared_families": sorted(set(families) & set(product.get("families", []))),
                "shared_accords": sorted(set(_top(vector["accord_weights"])) & set(product.get("accords", []))),
                "shared_moods": sorted(set(_top(vector["mood_weights"])) & set(product.get("moods", []))),
                "public_safe_explanation": "This match compares approved product metadata with selected scent preferences.",
            })
    family_text = ", ".join(value.replace("_", " ") for value in families) or "balanced"
    return {
        "scentprint_quiz_id": scored["scentprint_quiz_id"],
        "scentprint_public_alias": scored["scentprint_public_alias"],
        "result_title": "Your Scentprint Preference Guide",
        "result_summary": f"Your selections currently lean toward {family_text} scent families.",
        "dominant_families": families,
        "preferred_accords": _top(vector["accord_weights"]),
        "preferred_moods": _top(vector["mood_weights"]),
        "preferred_occasions": _top(vector["occasion_weights"]),
        "preferred_seasons": _top(vector["season_weights"]),
        "avoid_note_families": vector["avoid_note_families"],
        "recommended_product_matches": matches,
        "recommendation_explanations": [match["public_safe_explanation"] for match in matches],
        "confidence_band": scored["confidence_band"],
        "review_status": "demo_only" if demo_mode else "needs_human_review",
        "privacy_status": "public_safe_anonymous",
    }
