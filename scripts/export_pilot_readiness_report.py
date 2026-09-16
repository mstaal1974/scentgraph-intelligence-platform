#!/usr/bin/env python3
"""Export one deliberately limited CSV projection from a private run report."""

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_dir = Path("data/private/runs") / args.run_id
    report = json.loads((run_dir / "readiness.json").read_text(encoding="utf-8"))
    output = args.output or Path("data/samples") / f"{args.run_id}_readiness_summary.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run_id", "readiness_status", "privacy_audit_status", "launch_now_count",
              "enrichment_needed_count", "supplier_review_needed_count",
              "product_setup_needed_count", "hold_count", "pilot_recommendation"]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({field: report[field] for field in fields})
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
