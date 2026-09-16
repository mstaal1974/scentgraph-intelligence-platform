"""Private structured feedback with explicit public-safe projections."""

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.schemas.consumer_scent import ConsumerFeedbackCreate


@dataclass
class ConsumerFeedback:
    feedback_id: str
    scentprint_id: str
    fragrance_id: str | None
    product_id: str | None
    variant_id: str | None
    tried_format: str | None
    rating_band: str
    would_buy_full_size: bool | None
    would_buy_again: bool | None
    perceived_sweetness: str
    perceived_freshness: str
    perceived_darkness: str
    perceived_strength: str
    perceived_longevity: str
    perceived_projection: str
    perceived_occassions: list[str]
    perceived_seasons: list[str]
    perceived_moods: list[str]
    liked_notes: list[str]
    disliked_notes: list[str]
    free_text_private_note: str | None
    public_safe_quote: str | None
    review_status: str
    created_at: datetime


def create_feedback(payload: ConsumerFeedbackCreate) -> ConsumerFeedback:
    return ConsumerFeedback(feedback_id=str(uuid4()), **payload.model_dump(),
                            review_status="needs_human_review", created_at=datetime.now(UTC))


def public_safe_feedback(feedback: ConsumerFeedback) -> dict[str, object]:
    result = asdict(feedback)
    result.pop("scentprint_id")
    result.pop("free_text_private_note")
    if feedback.review_status != "approved":
        result["public_safe_quote"] = None
    return result


def _rate_band(values: list[bool | None]) -> str:
    known = [value for value in values if value is not None]
    if not known:
        return "unknown"
    rate = sum(known) / len(known)
    return "high" if rate >= .7 else "moderate" if rate >= .4 else "low"


def aggregate_feedback(feedback: list[ConsumerFeedback]) -> dict[str, object]:
    return {
        "feedback_count": len(feedback),
        "rating_bands": dict(Counter(item.rating_band for item in feedback)),
        "full_size_upgrade_rate_band": _rate_band([item.would_buy_full_size for item in feedback]),
        "repeat_purchase_intent_band": _rate_band([item.would_buy_again for item in feedback]),
    }


def scentprint_update_suggestions(feedback: ConsumerFeedback) -> dict[str, list[str]]:
    return {"preferred_notes": feedback.liked_notes, "disliked_notes": feedback.disliked_notes}
