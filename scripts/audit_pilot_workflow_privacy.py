#!/usr/bin/env python3
"""Reject confidential fields and personal records in public pilot CSV artifacts."""

import argparse
import csv
import re
from pathlib import Path

FORBIDDEN_FIELDS = {
    "supplier_price", "supplier_cost", "supplier_code", "cn_code", "stock", "quantity",
    "aed", "aed_price", "usd", "usd_price", "cost", "raw_margin", "margin",
    "commercial_terms", "supplier_commercial_terms", "seller_private_notes",
    "consumer_private_notes", "email", "phone", "phone_number", "address",
    "raw_individual_feedback",
}
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")


def audit_paths(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix.casefold() == ".csv":
            rows = csv.reader(text.splitlines())
            headers = next(rows, [])
            for header in headers:
                key = header.strip().casefold().replace(" ", "_").replace("-", "_")
                if key in FORBIDDEN_FIELDS:
                    violations.append(f"{path}: forbidden public field {header!r}")
        if EMAIL.search(text):
            violations.append(f"{path}: possible personal email")
        if PHONE.search(text):
            violations.append(f"{path}: possible personal phone number")
    return violations


def discover_public_pilot_files(root: Path) -> list[Path]:
    return sorted((root / "data/samples").glob("*pilot*.csv"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    paths = args.paths or discover_public_pilot_files(root)
    violations = audit_paths(paths)
    private = root / "data/private"
    for name in ("manifest.json", "readiness.json", "result.json"):
        for path in private.rglob(name) if private.exists() else []:
            if not path.is_relative_to(private / "runs"):
                violations.append(f"{path}: operational artifact is outside data/private/runs/")
    if violations:
        print("Pilot workflow privacy audit failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print(f"Pilot workflow privacy audit passed ({len(paths)} public files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
