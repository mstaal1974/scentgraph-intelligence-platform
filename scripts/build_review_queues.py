#!/usr/bin/env python3
"""Build private operational review queues from available JSON summaries."""

import argparse
import json
from collections import Counter
from pathlib import Path

from aromatwin.services.review_queue_builder import build_review_queues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="*", type=Path)
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/review_queue.json"))
    args = parser.parse_args()
    sources = {}
    for path in args.inputs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources.update(payload if isinstance(payload, dict) else {})
    queue = build_review_queues(sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    for label, field in (("gate", "gate_type"), ("priority", "priority_band"),
                         ("owner", "assigned_role")):
        print(f"{label}: {dict(Counter(str(item[field]) for item in queue))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

