"""Anonymous, thresholded aggregation of structured consumer feedback."""

from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.services.consumer_feedback import ConsumerFeedback, aggregate_feedback

MINIMUM_FEEDBACK = 3


def _common(items: list[ConsumerFeedback], attribute: str) -> list[str]:
    values = (value for item in items for value in getattr(item, attribute))
    return [value for value, _ in Counter(values).most_common(3)]


def _mode(items: list[ConsumerFeedback], attribute: str) -> str:
    values = [getattr(item, attribute) for item in items if getattr(item, attribute) != "unknown"]
    return Counter(values).most_common(1)[0][0] if values else "unknown"


def build_community_intelligence(
    feedback: list[ConsumerFeedback], *, fragrance_id: str | None = None,
    product_id: str | None = None, minimum_feedback: int = MINIMUM_FEEDBACK,
) -> dict[str, object]:
    selected = [item for item in feedback
                if (fragrance_id is None or item.fragrance_id == fragrance_id)
                and (product_id is None or item.product_id == product_id)]
    minimum_met = len(selected) >= minimum_feedback
    rates = aggregate_feedback(selected)
    confidence = "insufficient_data" if not minimum_met else "high" if len(selected) >= minimum_feedback * 3 else "moderate"
    summary = ("Minimum aggregation threshold not met."
               if not minimum_met else "Structured community signals are available as an additional, review-gated input.")
    return {
        "intelligence_id": str(uuid4()), "fragrance_id": fragrance_id,
        "product_id": product_id, "feedback_count": len(selected), "match_count": 0,
        "most_common_moods": _common(selected, "perceived_moods"),
        "most_common_occasions": _common(selected, "perceived_occassions"),
        "most_common_seasons": _common(selected, "perceived_seasons"),
        "perceived_strength_band": _mode(selected, "perceived_strength"),
        "perceived_longevity_band": _mode(selected, "perceived_longevity"),
        "perceived_projection_band": _mode(selected, "perceived_projection"),
        "full_size_upgrade_rate_band": rates["full_size_upgrade_rate_band"],
        "repeat_purchase_intent_band": rates["repeat_purchase_intent_band"],
        "scentprint_match_clusters": [], "community_summary": summary,
        "confidence_band": confidence, "minimum_feedback_met": minimum_met,
        "review_status": "needs_human_review", "updated_at": datetime.now(UTC),
    }


def public_summary(intelligence: dict[str, object]) -> dict[str, object]:
    allowed = {
        "fragrance_id", "product_id", "feedback_count", "most_common_moods",
        "most_common_occasions", "most_common_seasons", "perceived_strength_band",
        "perceived_longevity_band", "perceived_projection_band",
        "full_size_upgrade_rate_band", "repeat_purchase_intent_band", "community_summary",
        "confidence_band", "minimum_feedback_met",
    }
    return {key: value for key, value in intelligence.items() if key in allowed}
