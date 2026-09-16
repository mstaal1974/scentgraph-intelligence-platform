#!/usr/bin/env python3
"""Build thresholded operational intelligence without publishing individual records."""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.consumer_scent import ConsumerFeedbackCreate
from aromatwin.services.community_scent_intelligence import (
    build_community_intelligence,
    public_summary,
)
from aromatwin.services.consumer_feedback import create_feedback

ROOT = Path(__file__).resolve().parents[1]


def load_feedback(path: Path) -> list:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [create_feedback(ConsumerFeedbackCreate(**row)) for row in csv.DictReader(handle)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data/private/consumer_feedback.csv")
    parser.add_argument("--minimum-feedback", type=int, default=3)
    parser.add_argument("--write-sample", action="store_true")
    args = parser.parse_args()
    result = build_community_intelligence(load_feedback(args.input), minimum_feedback=args.minimum_feedback)
    report = ROOT / "data/private/reports/community_scent_intelligence.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, default=str, indent=2), encoding="utf-8")
    if args.write_sample:
        sample = ROOT / "data/samples/community_scent_intelligence_sample.csv"
        safe = public_summary(result)
        with sample.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(safe), lineterminator="\n")
            writer.writeheader()
            writer.writerow(safe)
    print(f"Built aggregate from {result['feedback_count']} feedback records")


if __name__ == "__main__":
    main()
