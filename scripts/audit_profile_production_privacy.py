#!/usr/bin/env python3
"""Audit public profile-production artifacts for private or copied fields."""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_GLOB = (ROOT / "data/samples").glob("*profile*")
DOCS = [ROOT / "docs/private-fragrance-profile-production.md"]
FORBIDDEN_FIELDS = {
    "supplier_price", "supplier_cost", "supplier_code", "cn_code", "aed_price", "usd_price",
    "raw_margin", "margin", "stock", "quantity", "commercial_terms", "seller_private_notes",
    "consumer_private_notes", "individual_feedback", "review_text", "review_rating", "comments",
    "rating", "image", "ugc", "private_source_path",
}
PATTERNS = {
    "credentialed database URL": re.compile(r"(?:postgres(?:ql)?|mysql)://[^\s/:]+:[^\s@]+@", re.I),
    "likely credential": re.compile(r"(?:api[_-]?key|password|private[_-]?key|access[_-]?token)\s*[:=]\s*[\"']?[A-Za-z0-9_\-/]{8,}", re.I),
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)"),
    "address": re.compile(r"\b\d{1,5}\s+[A-Za-z][A-Za-z ]+\s(?:Street|St|Road|Rd|Avenue|Ave)\b", re.I),
}


def audit_paths(paths: list[Path]) -> list[str]:
    violations = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".csv":
            headers = {value.strip().casefold() for value in next(csv.reader(text.splitlines()), [])}
            for field in sorted(headers & FORBIDDEN_FIELDS):
                violations.append(f"{path}: forbidden public field {field}")
            if "profile_draft_id" in headers and "fictional" not in text.casefold():
                violations.append(f"{path}: profile draft sample is not explicitly fictional")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{path}: {label}")
    return violations


def main() -> int:
    paths = sorted(SAMPLE_GLOB) + DOCS
    violations = audit_paths(paths)
    if violations:
        print("FAIL: profile production privacy audit")
        print("\n".join(violations))
        return 1
    print(f"PASS: profile production privacy audit ({len(paths)} public files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
