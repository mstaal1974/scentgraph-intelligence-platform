#!/usr/bin/env python3
"""Reject sensitive column names or personal-data indicators in public pilot samples."""

import csv
import sys
from pathlib import Path

FORBIDDEN = {"code", "cn", "qty", "aed", "usd", "usd $", "price", "cost", "margin",
             "supplier_price", "supplier_cost", "raw_margin", "aed_price", "usd_price",
             "stock", "quantity", "cn_code", "supplier_code", "commercial_terms",
             "seller_private_notes", "consumer_private_notes", "email", "phone", "address",
             "raw_individual_feedback"}


def audit_paths(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        if not path.exists() or path.suffix.lower() != ".csv":
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            headers = {cell.strip().lower() for cell in next(reader, [])}
        found = sorted(headers & FORBIDDEN)
        if found:
            violations.append(f"{path}: forbidden public fields: {', '.join(found)}")
    return violations


def main() -> int:
    samples = sorted(Path("data/samples").glob("*.csv"))
    configured = Path("data/private/imports").resolve()
    if not configured.is_relative_to((Path("data").resolve() / "private")):
        print("configured input path is outside data/private/", file=sys.stderr)
        return 1
    violations = audit_paths(samples)
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print(f"Private pilot audit passed for {len(samples)} public-safe sample files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
