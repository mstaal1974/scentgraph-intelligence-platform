#!/usr/bin/env python3
"""Reject sensitive field names and personal identifiers in public completion CSV files."""

import csv
import re
import sys
from pathlib import Path

FORBIDDEN_HEADERS = {
    "supplier_price", "supplier_cost", "raw_margin", "aed_price", "usd_price", "stock",
    "quantity", "cn_code", "supplier_code", "commercial_terms", "seller_private_notes",
    "consumer_private_notes", "email", "phone", "address", "raw_individual_feedback",
}
PERSONAL_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:\+?\d[\d ()-]{7,}\d)\b"),
)
FORBIDDEN_PHRASES = {
    "supplier price", "supplier cost", "raw margin", "aed price", "usd price", "cn code",
    "supplier code", "supplier commercial terms", "seller private notes",
    "consumer private notes", "raw individual feedback",
}


def audit_paths(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        if not path.is_file() or path.suffix.lower() != ".csv":
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        headers = {cell.strip().lower() for cell in (rows[0] if rows else [])}
        found = sorted(headers & FORBIDDEN_HEADERS)
        if found:
            violations.append(f"{path}: forbidden public fields: {', '.join(found)}")
        body = "\n".join(",".join(row) for row in rows[1:])
        normalised_body = body.lower().replace("_", "-").replace("-", " ")
        phrases = sorted(phrase for phrase in FORBIDDEN_PHRASES if phrase in normalised_body)
        if phrases:
            violations.append(f"{path}: forbidden public content categories detected")
        if any(pattern.search(body) for pattern in PERSONAL_PATTERNS):
            violations.append(f"{path}: possible personal identifier in public output")
    return violations


def main() -> int:
    samples = sorted(Path("data/samples").glob("*platform*completion*.csv"))
    samples += sorted(Path("data/samples").glob("final_platform_readiness*.csv"))
    violations = audit_paths(samples)
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print(f"Platform completion privacy audit passed for {len(samples)} public-safe files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
