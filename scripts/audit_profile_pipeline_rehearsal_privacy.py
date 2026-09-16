#!/usr/bin/env python3
"""Fail closed when public rehearsal artifacts contain private-shaped data."""

import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {
    "supplier_price",
    "supplier_cost",
    "supplier_code",
    "cn_code",
    "aed_price",
    "usd_price",
    "cost",
    "raw_margin",
    "margin",
    "stock",
    "quantity",
    "commercial_terms",
    "seller_private_notes",
    "consumer_private_notes",
    "review_text",
    "review",
    "rating",
    "comment",
    "comments",
    "image",
    "ugc",
    "email",
    "phone",
    "address",
    "password",
    "token",
    "api_key",
    "private_api_key",
}
PATTERNS = {
    "credentialed database URL": re.compile(r"(?:postgres(?:ql)?|mysql)://[^\s/:]+:[^\s@]+@", re.I),
    "likely secret": re.compile(
        r"(?:api[_-]?key|password|access[_-]?token|private[_-]?key)\s*[:=]\s*[\"']?[A-Za-z0-9_\-/]{8,}",
        re.I,
    ),
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)"),
    "postal address": re.compile(r"\b\d{1,5}\s+[A-Za-z][A-Za-z ]+\s(?:Street|Road|Avenue)\b", re.I),
}


def audit_paths(paths):
    violations = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".csv":
            headers = {h.strip().casefold() for h in next(csv.reader(text.splitlines()), [])}
            for field in sorted(headers & FORBIDDEN):
                violations.append(f"{path}: forbidden public field {field}")
            if "profile_draft_id" in headers:
                violations.append(f"{path}: profile drafts are forbidden in public samples")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{path}: {label}")
    return violations


def main():
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="*", type=Path)
    a = p.parse_args()
    paths = a.paths or sorted((ROOT / "data/samples").glob("profile_pipeline_*.csv")) + [
        ROOT / "docs/profile-pipeline-rehearsal.md"
    ]
    violations = audit_paths(paths)
    if violations:
        print("FAIL: profile pipeline rehearsal privacy audit\n" + "\n".join(map(str, violations)))
        return 1
    print(f"PASS: profile pipeline rehearsal privacy audit ({len(paths)} public files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
