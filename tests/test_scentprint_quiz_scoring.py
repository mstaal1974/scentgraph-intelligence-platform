from aromatwin.services.scentprint_quiz_scoring import score_quiz_responses
from scripts.build_scentprint_quiz_samples import SAMPLE_RESPONSES


def test_scoring_returns_bands_weights_and_no_raw_text():
    result = score_quiz_responses("quiz_demo001", SAMPLE_RESPONSES)
    vector = result["preference_vector"]
    assert vector["scent_family_weights"] == {"citrus": 1.0, "woody": 0.5}
    assert vector["sweetness_band"] == "low"
    assert vector["freshness_band"] == "high"
    assert result["confidence_band"] == "high"
    assert "raw" not in str(result).casefold()
    assert "answer" not in result


def test_scoring_is_stateless_and_rejects_unknown_options():
    first = score_quiz_responses("quiz_demo001", SAMPLE_RESPONSES)
    second = score_quiz_responses("quiz_demo001", SAMPLE_RESPONSES)
    assert first["scentprint_quiz_id"] == second["scentprint_quiz_id"]
    try:
        score_quiz_responses("quiz_demo001", [{"question_id": "family",
                                               "selected_option_ids": ["invented"]}])
    except ValueError as exc:
        assert "Invalid option" in str(exc)
    else:
        raise AssertionError("unknown option was accepted")
