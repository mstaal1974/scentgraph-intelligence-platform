"""Versioned, deterministic and public-safe Scentprint quiz contract."""

from copy import deepcopy

QUIZ_CONTRACT_VERSION = "1.0.0"
ANSWER_TYPES = {"single_choice", "multi_choice", "scale", "ranked_choice", "free_text_disabled"}
SCORING_DIMENSIONS = {
    "scent_family_weights", "note_family_weights", "accord_weights", "mood_weights",
    "occasion_weights", "season_weights", "intensity_band", "sweetness_band",
    "freshness_band", "warmth_band", "projection_band", "longevity_band",
    "avoid_note_families", "discovery_preference_band",
}


def _options(*values: str) -> list[dict[str, str]]:
    return [{"option_id": value, "label": value.replace("_", " ").title()} for value in values]


def _question(
    question_id: str,
    section: str,
    text: str,
    answer_type: str,
    options: list[dict[str, str]],
    dimensions: list[str],
    *,
    required: bool = True,
) -> dict[str, object]:
    return {
        "question_id": question_id,
        "section": section,
        "question_text": text,
        "answer_type": answer_type,
        "options": options,
        "scoring_dimensions": dimensions,
        "required": required,
        "public_safe_hint": "Choose only from the listed scent-preference options.",
        "privacy_note": "No identity, contact, demographic, or open-ended response is requested.",
    }


QUESTIONS = (
    _question("family", "scent_family_preference", "Which scent families appeal to you?",
              "multi_choice", _options("citrus", "floral", "woody", "amber", "fresh", "gourmand"),
              ["scent_family_weights"]),
    _question("intensity", "intensity_preference", "Which scent intensity do you prefer?",
              "single_choice", _options("light", "balanced", "bold"), ["intensity_band"]),
    _question("fresh_warm", "freshness_warmth_preference", "Where is your preferred balance?",
              "single_choice", _options("fresh", "balanced", "warm"),
              ["freshness_band", "warmth_band"]),
    _question("sweetness", "sweetness_preference", "How sweet should the scent profile feel?",
              "scale", _options("1", "2", "3", "4", "5"), ["sweetness_band"]),
    _question("woody", "woody_resinous_preference", "Which woody or resinous styles appeal?",
              "multi_choice", _options("dry_woods", "soft_woods", "resinous", "none"),
              ["note_family_weights", "accord_weights"]),
    _question("floral", "floral_preference", "Which floral styles appeal?", "multi_choice",
              _options("soft_floral", "white_floral", "rose_style", "none"),
              ["note_family_weights", "accord_weights"]),
    _question("citrus", "citrus_fresh_preference", "Which citrus or fresh styles appeal?",
              "multi_choice", _options("bright_citrus", "green_fresh", "aquatic_fresh", "none"),
              ["note_family_weights", "accord_weights"]),
    _question("gourmand", "gourmand_preference", "Which gourmand styles appeal?",
              "multi_choice", _options("vanilla_style", "cocoa_style", "caramel_style", "none"),
              ["note_family_weights", "accord_weights"]),
    _question("occasion", "occasion_preference", "When would you most like to wear the scent?",
              "ranked_choice", _options("everyday", "evening", "special_occasion", "outdoors"),
              ["occasion_weights"]),
    _question("season", "season_preference", "Which seasons should the scent complement?",
              "multi_choice", _options("spring", "summer", "autumn", "winter"), ["season_weights"]),
    _question("mood", "mood_preference", "Which scent moods appeal to you?", "multi_choice",
              _options("bright", "calm", "cosy", "elegant", "adventurous"), ["mood_weights"]),
    _question("projection", "projection_preference", "How noticeable should the scent be nearby?",
              "single_choice", _options("close", "balanced", "noticeable"), ["projection_band"]),
    _question("longevity", "longevity_preference", "What wear-duration preference should guide matches?",
              "single_choice", _options("short", "moderate", "long"), ["longevity_band"]),
    _question("discovery", "discovery_style", "How familiar or exploratory should suggestions be?",
              "single_choice", _options("familiar", "balanced", "exploratory"),
              ["discovery_preference_band"]),
    _question("avoid", "avoid_notes", "Which listed note families should suggestions avoid?",
              "multi_choice", _options("smoky", "powdery", "animalic", "gourmand", "none"),
              ["avoid_note_families"], required=False),
)


def get_quiz_contract() -> dict[str, object]:
    """Return a defensive copy so callers cannot mutate the canonical contract."""
    return {
        "contract_id": "scentprint-quiz",
        "quiz_contract_version": QUIZ_CONTRACT_VERSION,
        "title": "Scentprint Preference Quiz",
        "purpose": "Anonymous scent-preference guidance only; not identity or diagnosis.",
        "questions": deepcopy(list(QUESTIONS)),
        "privacy_status": "public_safe_anonymous",
    }


def validate_quiz_contract(contract: dict[str, object] | None = None) -> list[str]:
    contract = contract or get_quiz_contract()
    errors: list[str] = []
    questions = contract.get("questions", [])
    if not isinstance(questions, list):
        return ["questions must be a list"]
    forbidden = {"name", "email", "phone", "address", "age", "gender", "ethnicity", "health",
                 "medical", "biometric", "identity"}
    for question in questions:
        answer_type = str(question.get("answer_type", ""))
        if answer_type not in ANSWER_TYPES or answer_type == "free_text_disabled":
            errors.append(f"{question.get('question_id')}: open-ended or disabled answer type")
        unknown = set(question.get("scoring_dimensions", [])) - SCORING_DIMENSIONS
        if unknown:
            errors.append(f"{question.get('question_id')}: unknown dimensions {sorted(unknown)}")
        words = set(str(question.get("question_text", "")).casefold().replace("?", "").split())
        if words & forbidden:
            errors.append(f"{question.get('question_id')}: sensitive question")
        if not question.get("options"):
            errors.append(f"{question.get('question_id')}: options required")
    return errors
