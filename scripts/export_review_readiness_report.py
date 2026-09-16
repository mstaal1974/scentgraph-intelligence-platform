#!/usr/bin/env python3
"""Export count/status-only review readiness."""

import argparse
import json
from pathlib import Path

from aromatwin.services.review_readiness import build_review_readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path,
                        default=Path("data/private/reports/review_queue.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/review_readiness.json"))
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8")) if args.queue.exists() else []
    report = build_review_readiness(queue)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Exported aggregate readiness for {report['total_items']} review items.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
