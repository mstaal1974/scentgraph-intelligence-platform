#!/usr/bin/env python3
"""Export the non-secret API entitlement contract."""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aromatwin.services.api_entitlements import build_api_entitlement_matrix  # noqa: E402

FIELDS = ["plan_id", "api_group", "allowed", "access_level", "usage_limit", "public_safe_reason"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [{field: getattr(item, field) for field in FIELDS}
            for item in build_api_entitlement_matrix().entitlements]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.lower() == ".json":
        args.output.write_text(json.dumps(rows, indent=2) + "\n")
    elif args.output.suffix.lower() == ".csv":
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    else:
        parser.error("output must end in .csv or .json")
    print(f"Exported {len(rows)} public-safe entitlement rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
