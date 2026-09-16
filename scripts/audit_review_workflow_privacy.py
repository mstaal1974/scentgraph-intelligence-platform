#!/usr/bin/env python3
"""Fail when public review-workflow artifacts expose private or commercial fields."""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

FORBIDDEN_FIELDS = {
    "supplier_price", "supplier_cost", "supplier_code", "cn_code", "stock", "quantity",
    "aed", "aed_price", "usd", "usd_price", "cost", "raw_margin", "margin",
    "commercial_terms", "supplier_commercial_terms", "seller_private_notes",
    "consumer_private_notes", "consumer_email", "consumer_phone", "email", "phone",
    "phone_number", "address", "raw_individual_feedback", "decision_reason",
}
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return list(value) + [key for child in value.values() for key in _keys(child)]
    if isinstance(value, list):
        return [key for child in value for key in _keys(child)]
    return []


def audit_paths(paths: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        fields: list[str] = []
        if path.suffix.casefold() == ".csv":
            fields = next(csv.reader(text.splitlines()), [])
        elif path.suffix.casefold() == ".json":
            try:
                fields = _keys(json.loads(text))
            except json.JSONDecodeError:
                violations.append(f"{path}: invalid JSON")
        for field in fields:
            if _normalise(field) in FORBIDDEN_FIELDS:
                violations.append(f"{path}: forbidden public field {field!r}")
        if EMAIL.search(text):
            violations.append(f"{path}: possible personal email")
        if PHONE.search(text):
            violations.append(f"{path}: possible personal phone number")
    return violations


def discover(root: Path) -> list[Path]:
    return sorted((root / "data" / "samples").glob("*review*.csv")) + sorted(
        (root / "data" / "samples").glob("*review*.json")
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or discover(Path.cwd())
    violations = audit_paths(paths)
    if violations:
        print("Review workflow privacy audit failed:")
        print("\n".join(f"- {item}" for item in violations))
        return 1
    print(f"Review workflow privacy audit passed ({len(paths)} public files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

