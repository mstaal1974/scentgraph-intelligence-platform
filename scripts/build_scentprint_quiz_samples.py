#!/usr/bin/env python3
"""Build fictional, public-safe Scentprint quiz CSV examples."""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aromatwin.services.scentprint_quiz_contracts import get_quiz_contract  # noqa: E402
from aromatwin.services.scentprint_quiz_results import build_quiz_result  # noqa: E402
from aromatwin.services.scentprint_quiz_scoring import score_quiz_responses  # noqa: E402

SAMPLE_RESPONSES = [
    {"question_id": "family", "selected_option_ids": ["citrus", "woody"]},
    {"question_id": "intensity", "selected_option_ids": "balanced"},
    {"question_id": "fresh_warm", "selected_option_ids": "fresh"},
    {"question_id": "sweetness", "selected_option_ids": "2"},
    {"question_id": "woody", "selected_option_ids": ["dry_woods"]},
    {"question_id": "floral", "selected_option_ids": ["soft_floral"]},
    {"question_id": "citrus", "selected_option_ids": ["bright_citrus"]},
    {"question_id": "gourmand", "selected_option_ids": ["none"]},
    {"question_id": "occasion", "selected_option_ids": ["everyday", "outdoors"]},
    {"question_id": "season", "selected_option_ids": ["spring", "summer"]},
    {"question_id": "mood", "selected_option_ids": ["bright", "calm"]},
    {"question_id": "projection", "selected_option_ids": "balanced"},
    {"question_id": "longevity", "selected_option_ids": "moderate"},
    {"question_id": "discovery", "selected_option_ids": "balanced"},
    {"question_id": "avoid", "selected_option_ids": ["smoky"]},
]


def _write(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key], sort_keys=True) if isinstance(row.get(key), (list, dict))
                             else row.get(key, "") for key in fields})


def build(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    questions = get_quiz_contract()["questions"]
    _write(output / "scentprint_quiz_questions_sample.csv", questions,
           ["question_id", "section", "question_text", "answer_type", "options",
            "scoring_dimensions", "required", "public_safe_hint", "privacy_note"])
    response_rows = [{"scentprint_public_alias": "quiz_demo001", **row} for row in SAMPLE_RESPONSES]
    _write(output / "scentprint_quiz_response_sample.csv", response_rows,
           ["scentprint_public_alias", "question_id", "selected_option_ids"])
    scored = score_quiz_responses("quiz_demo001", SAMPLE_RESPONSES)
    result = build_quiz_result(scored, demo_mode=True)
    _write(output / "scentprint_quiz_result_sample.csv", [result],
           ["scentprint_quiz_id", "scentprint_public_alias", "result_title", "result_summary",
            "dominant_families", "preferred_accords", "preferred_moods", "preferred_occasions",
            "preferred_seasons", "avoid_note_families", "confidence_band", "review_status",
            "privacy_status"])
    _write(output / "scentprint_quiz_product_match_sample.csv",
           result["recommended_product_matches"],
           ["product_id", "product_title", "product_format", "match_score_band", "match_reason",
            "shared_families", "shared_accords", "shared_moods", "public_safe_explanation"])


if __name__ == "__main__":
    build(Path("data/samples"))
    print("Wrote fictional public-safe Scentprint quiz samples to data/samples")
