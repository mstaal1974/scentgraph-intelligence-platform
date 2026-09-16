#!/usr/bin/env python3
"""Export public-safe proposed plan summaries as CSV or JSON."""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aromatwin.schemas.commercial_packaging import CommercialPlanPublicSummary  # noqa: E402
from aromatwin.services.commercial_plans import get_commercial_plans  # noqa: E402


def rows() -> list[dict[str, object]]:
    return [CommercialPlanPublicSummary.model_validate(
            p.model_dump(include=set(CommercialPlanPublicSummary.model_fields))).model_dump()
            for p in get_commercial_plans()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = rows()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.lower() == ".json":
        args.output.write_text(json.dumps(data, indent=2) + "\n")
    elif args.output.suffix.lower() == ".csv":
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=data[0])
            writer.writeheader()
            writer.writerows({k: "|".join(v) if isinstance(v, list) else v for k, v in row.items()}
                             for row in data)
    else:
        parser.error("output must end in .csv or .json")
    print(f"Exported {len(data)} public-safe plan examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
