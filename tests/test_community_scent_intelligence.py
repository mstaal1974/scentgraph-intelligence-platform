from aromatwin.schemas.consumer_scent import ConsumerFeedbackCreate
from aromatwin.services.community_scent_intelligence import (
    build_community_intelligence,
    public_summary,
)
from aromatwin.services.consumer_feedback import create_feedback


def feedback(profile_id: str):
    return create_feedback(ConsumerFeedbackCreate(
        scentprint_id=profile_id, fragrance_id="f-1", perceived_moods=["calm"],
        perceived_occassions=["evening"], perceived_seasons=["autumn"],
        perceived_strength="moderate", would_buy_full_size=True,
    ))


def test_community_aggregation_has_no_individuals() -> None:
    result = public_summary(build_community_intelligence(
        [feedback("p-1"), feedback("p-2"), feedback("p-3")], fragrance_id="f-1"))
    assert result["feedback_count"] == 3
    assert result["minimum_feedback_met"] is True
    assert "scentprint_id" not in str(result)
    assert "feedback_id" not in str(result)


def test_community_marks_insufficient_data() -> None:
    result = build_community_intelligence([feedback("p-1")], fragrance_id="f-1")
    assert result["minimum_feedback_met"] is False
    assert result["confidence_band"] == "insufficient_data"
