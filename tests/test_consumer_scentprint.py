from aromatwin.schemas.consumer_scent import ConsumerScentprintCreate
from aromatwin.services.consumer_scentprint import (
    create_scentprint,
    match_scent_profile,
    public_summary,
)


def profile():
    return create_scentprint(ConsumerScentprintCreate(
        consumer_public_alias="Explorer_001", preferred_families=["woody"],
        preferred_notes=["cedar"], disliked_notes=["rose"], preferred_moods=["calm"],
        preferred_occasions=["evening"], preferred_seasons=["autumn"],
        preferred_product_formats=["tester"],
    ))


def test_scentprint_creation_from_structured_preferences() -> None:
    result = profile()
    assert result.preferred_families == ["woody"]
    assert result.review_status == "needs_human_review"


def test_public_summary_excludes_private_consumer_data() -> None:
    result = public_summary(profile())
    assert "scentprint_id" not in result
    assert "known_likes" not in result
    assert set(result) == {"consumer_public_alias", "preferred_families", "preferred_moods",
                           "preferred_occasions", "preferred_seasons",
                           "preferred_product_formats", "privacy_status"}


def test_matching_returns_explainable_match_band() -> None:
    result = match_scent_profile(profile(), {"id": "fragrance-1", "families": ["woody"],
                                                    "notes": ["cedar"], "moods": ["calm"]})
    assert result["match_band"] in {"weak", "moderate", "strong", "excellent"}
    assert result["reasons"]
    assert "private" not in str(result).lower()
