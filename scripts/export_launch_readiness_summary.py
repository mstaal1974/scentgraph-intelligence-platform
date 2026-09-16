#!/usr/bin/env python3
"""Export an allow-listed, public-safe launch readiness summary."""
import argparse
import json
from pathlib import Path

from aromatwin.services.launch_intelligence import public_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/private/reports/launch_priority.json"))
    parser.add_argument("--output", type=Path, default=Path("data/private/reports/launch_readiness_summary.json"))
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8")) if args.input.exists() else []
    summaries = [public_summary(record) for record in records]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summaries, default=str, indent=2), encoding="utf-8")
    print(f"Exported {len(summaries)} public-safe summaries")

if __name__ == "__main__":
    main()
