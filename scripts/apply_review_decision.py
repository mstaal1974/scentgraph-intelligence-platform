#!/usr/bin/env python3
"""Record one private review decision without triggering downstream actions."""

import argparse
import json
from pathlib import Path

from aromatwin.services.review_decisions import apply_review_decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review_item_id")
    parser.add_argument("decision")
    parser.add_argument("reviewer_role")
    parser.add_argument("--decision-reason")
    parser.add_argument("--queue", type=Path,
                        default=Path("data/private/reports/review_queue.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/review_decisions.json"))
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    item = next((row for row in queue if row["review_item_id"] == args.review_item_id), None)
    if item is None:
        parser.error("review item not found")
    decision = apply_review_decision(item, args.decision, args.reviewer_role,
                                     decision_reason=args.decision_reason)
    existing = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else []
    if not any(row["decision_id"] == decision["decision_id"] for row in existing):
        existing.append(decision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {decision['decision_id']} for internal workflow only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

