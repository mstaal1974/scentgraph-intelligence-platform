#!/usr/bin/env python3
"""Generate fictional, public-safe consumer scent samples under data/samples only."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"


def write(name: str, rows: list[dict[str, object]]) -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    with (SAMPLES / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    write("consumer_scentprint_sample.csv", [
        {"anonymous_alias": "ScentExplorer_01", "preferred_family": "woody",
         "preferred_mood": "calm", "occasion": "evening", "season": "autumn",
         "product_format_preference": "tester", "match_band": "strong"},
        {"anonymous_alias": "ScentExplorer_02", "preferred_family": "fresh",
         "preferred_mood": "bright", "occasion": "everyday", "season": "spring",
         "product_format_preference": "bottle", "match_band": "moderate"},
    ])
    write("consumer_feedback_sample.csv", [
        {"rating_band": "good", "would_buy_band": "high", "perceived_strength_band": "moderate",
         "season": "autumn", "mood": "calm", "review_status": "needs_human_review"},
    ])
    write("scent_wardrobe_sample.csv", [
        {"anonymous_alias": "ScentExplorer_01", "status": "wants_to_try",
         "usage_context": "evening", "next_action": "try tester"},
    ])


if __name__ == "__main__":
    main()
