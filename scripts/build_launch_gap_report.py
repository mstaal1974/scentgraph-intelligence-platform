#!/usr/bin/env python3
"""Build an owner- and severity-grouped operational launch gap report."""
import argparse
import json
from collections import Counter
from pathlib import Path

from aromatwin.services.launch_gap_analysis import analyse_launch_gaps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/private/reports/launch_priority.json"))
    parser.add_argument("--output", type=Path, default=Path("data/private/reports/launch_gaps.json"))
    parser.add_argument("--public-output", type=Path)
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8")) if args.input.exists() else []
    gaps = [gap for record in records for gap in analyse_launch_gaps(record)]
    report = {"gap_count": len(gaps), "by_owner_role": dict(Counter(g["owner_role"] for g in gaps)),
              "by_severity": dict(Counter(g["severity"] for g in gaps)), "gaps": gaps}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.public_output:
        if args.public_output.parent != Path("data/samples"):
            raise SystemExit("Public demo output must be written directly under data/samples/")
        args.public_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("by_owner_role:", report["by_owner_role"])
    print("by_severity:", report["by_severity"])

if __name__ == "__main__":
    main()
