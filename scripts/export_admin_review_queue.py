#!/usr/bin/env python3
"""Export the public/admin-safe human review queue from allowlisted CSV metadata."""

import argparse
import csv
from collections import Counter
from pathlib import Path

from aromatwin.services.admin_review import build_review_queue, export_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("data/admin_review_queue.csv"))
    args = parser.parse_args()
    rows = export_rows(build_review_queue(args.data_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "stage", "record_id", "title", "status", "confidence", "provenance_summary",
        "blocking_reason", "next_action",
    )
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter("rejected" if str(row["status"]).startswith("rejected") else "accepted"
                     for row in rows)
    print(f"Exported {len(rows)} safe rows to {args.output}")
    print(f"accepted={counts['accepted']} rejected={counts['rejected']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
