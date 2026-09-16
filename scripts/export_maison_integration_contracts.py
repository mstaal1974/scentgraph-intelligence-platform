#!/usr/bin/env python3
"""Export allow-listed contract field documentation (never source records)."""
import argparse
import csv
import json
from pathlib import Path

from aromatwin.services.maison_export_contracts import contract_fields


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/maison/contracts.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        args.output.write_text(json.dumps(contract_fields(), indent=2) + "\n")
    else:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["contract", "field"])
            writer.writerows((name, field) for name, fields in contract_fields().items() for field in fields)
    print(f"Wrote public-safe contract documentation: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
