"""Stateless conversion of allowlisted quiz choices into preference guidance."""

import hashlib
import json
from datetime import UTC, datetime

from aromatwin.services.scentprint_quiz_contracts import QUIZ_CONTRACT_VERSION, get_quiz_contract

WEIGHT_QUESTIONS = {
    "family": "scent_family_weights", "woody": "note_family_weights",
    "floral": "note_family_weights", "citrus": "note_family_weights",
    "gourmand": "note_family_weights", "mood": "mood_weights",
    "occasion": "occasion_weights", "season": "season_weights",
}
BAND_QUESTIONS = {
    "intensity": "intensity_band", "sweetness": "sweetness_band",
    "projection": "projection_band", "longevity": "longevity_band",
    "discovery": "discovery_preference_band",
}


def _values(answer: object) -> list[str]:
    if isinstance(answer, list):
        return [str(value) for value in answer]
    return [str(answer)] if answer is not None else []


def _scale_band(value: str) -> str:
    try:
        score = int(value)
    except ValueError:
        return "unknown"
    return "low" if score <= 2 else "moderate" if score == 3 else "high"


def score_quiz_responses(public_alias: str, responses: list[dict[str, object]]) -> dict[str, object]:
    """Score selected option IDs only. Nothing is persisted by this function."""
    contract = get_quiz_contract()
    questions = {item["question_id"]: item for item in contract["questions"]}
    selected: dict[str, list[str]] = {}
    for response in responses:
        question_id = str(response.get("question_id", ""))
        if question_id not in questions:
            raise ValueError(f"Unknown question_id: {question_id}")
        allowed = {item["option_id"] for item in questions[question_id]["options"]}
        values = _values(response.get("selected_option_ids"))
        if not values or not set(values) <= allowed:
            raise ValueError(f"Invalid option for question_id: {question_id}")
        selected[question_id] = values

    vector: dict[str, object] = {
        "scent_family_weights": {}, "note_family_weights": {}, "accord_weights": {},
        "mood_weights": {}, "occasion_weights": {}, "season_weights": {},
        "intensity_band": "unknown", "sweetness_band": "unknown",
        "freshness_band": "unknown", "warmth_band": "unknown",
        "projection_band": "unknown", "longevity_band": "unknown",
        "avoid_note_families": [], "discovery_preference_band": "unknown",
    }
    for question_id, dimension in WEIGHT_QUESTIONS.items():
        values = [value for value in selected.get(question_id, []) if value != "none"]
        if values:
            size = len(values)
            vector[dimension] = {value: round((size - index) / size, 3)
                                 for index, value in enumerate(values)}
            if question_id in {"woody", "floral", "citrus", "gourmand"}:
                vector["accord_weights"].update(vector[dimension])
    for question_id, dimension in BAND_QUESTIONS.items():
        if question_id in selected:
            value = selected[question_id][0]
            vector[dimension] = _scale_band(value) if question_id == "sweetness" else value
    fresh_warm = selected.get("fresh_warm", ["unknown"])[0]
    vector["freshness_band"] = "high" if fresh_warm == "fresh" else "low" if fresh_warm == "warm" else fresh_warm
    vector["warmth_band"] = "high" if fresh_warm == "warm" else "low" if fresh_warm == "fresh" else fresh_warm
    vector["avoid_note_families"] = [v for v in selected.get("avoid", []) if v != "none"]

    required = {item["question_id"] for item in contract["questions"] if item["required"]}
    all_ids = set(questions)
    missing = len(required - set(selected))
    skipped = len(all_ids - set(selected))
    answered_required = len(required & set(selected))
    completion = answered_required / len(required)
    confidence = "high" if completion == 1 else "moderate" if completion >= .7 else "low"
    fingerprint = json.dumps({"alias": public_alias, "selected": selected}, sort_keys=True)
    quiz_id = "spq_" + hashlib.sha256(fingerprint.encode()).hexdigest()[:12]
    return {
        "scentprint_quiz_id": quiz_id,
        "quiz_contract_version": QUIZ_CONTRACT_VERSION,
        "scentprint_public_alias": public_alias,
        "preference_vector": vector,
        "confidence_band": confidence,
        "missing_response_count": missing,
        "skipped_question_count": skipped,
        "privacy_status": "public_safe_anonymous",
        "created_at": datetime.now(UTC),
    }
