from aromatwin.schemas.consumer_scent import ConsumerFeedbackCreate
from aromatwin.services.consumer_feedback import create_feedback, public_safe_feedback


def test_feedback_public_projection_hides_note_and_identity() -> None:
    record = create_feedback(ConsumerFeedbackCreate(
        scentprint_id="private-profile", fragrance_id="fragrance-1",
        free_text_private_note="For my own records", public_safe_quote="Optional original quote",
    ))
    public = public_safe_feedback(record)
    assert "free_text_private_note" not in public
    assert "scentprint_id" not in public
    assert public["public_safe_quote"] is None


def test_feedback_does_not_auto_publish_quote() -> None:
    record = create_feedback(ConsumerFeedbackCreate(scentprint_id="profile-1", public_safe_quote="Nice"))
    assert record.review_status == "needs_human_review"
    assert public_safe_feedback(record)["public_safe_quote"] is None
