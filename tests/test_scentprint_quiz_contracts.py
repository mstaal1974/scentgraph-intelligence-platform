from aromatwin.services.scentprint_quiz_contracts import get_quiz_contract, validate_quiz_contract


def test_contract_has_every_required_section_and_is_valid():
    expected = {"scent_family_preference", "intensity_preference", "freshness_warmth_preference",
                "sweetness_preference", "woody_resinous_preference", "floral_preference",
                "citrus_fresh_preference", "gourmand_preference", "occasion_preference",
                "season_preference", "mood_preference", "projection_preference",
                "longevity_preference", "discovery_style", "avoid_notes"}
    contract = get_quiz_contract()
    assert {question["section"] for question in contract["questions"]} == expected
    assert validate_quiz_contract(contract) == []


def test_contract_never_enables_free_text_or_sensitive_questions():
    serialized = str(get_quiz_contract()).casefold()
    assert "'answer_type': 'free_text" not in serialized
    for question in get_quiz_contract()["questions"]:
        assert question["options"]
        assert not ({"email", "phone", "address", "age", "gender", "ethnicity", "health"}
                    & set(question["question_text"].casefold().split()))
