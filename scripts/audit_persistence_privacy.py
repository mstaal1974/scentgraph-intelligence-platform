#!/usr/bin/env python3
"""Reject sensitive columns and personal identifiers in public persistence exports."""

import argparse
import csv
import re
from pathlib import Path

FORBIDDEN_FIELDS = {
    "supplier_price",
    "supplier_cost",
    "supplier_code",
    "cn_code",
    "stock",
    "quantity",
    "aed",
    "aed_price",
    "usd",
    "usd_price",
    "cost",
    "raw_margin",
    "margin",
    "commercial_terms",
    "supplier_commercial_terms",
    "seller_private_notes",
    "consumer_private_notes",
    "email",
    "phone",
    "phone_number",
    "address",
    "raw_individual_feedback",
}
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")


def audit_paths(paths: list[Path]) -> list[str]:
    violations = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix.casefold() in {".csv", ".json"}:
            headers = next(csv.reader(text.splitlines()), []) if path.suffix == ".csv" else []
            for header in headers:
                normalised = header.strip().casefold().replace(" ", "_").replace("-", "_")
                if normalised in FORBIDDEN_FIELDS:
                    violations.append(f"{path}: forbidden public field {header!r}")
        if EMAIL.search(text):
            violations.append(f"{path}: possible personal email")
        if PHONE.search(text):
            violations.append(f"{path}: possible personal phone number")
    return violations


def discover(root: Path) -> list[Path]:
    return sorted((root / "data/samples").glob("*persistence*.csv")) + sorted(
        (root / "data/samples").glob("*operational_audit*.csv")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or discover(Path.cwd())
    violations = audit_paths(paths)
    if violations:
        print("Persistence privacy audit failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print(f"Persistence privacy audit passed ({len(paths)} public files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
