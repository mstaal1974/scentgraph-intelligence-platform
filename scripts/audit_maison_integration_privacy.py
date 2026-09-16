#!/usr/bin/env python3
"""Conservative audit for public Maison samples and generated public exports."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = [*sorted((ROOT / "data/samples").glob("maison_*"))]
FORBIDDEN_HEADERS = {
    "supplier_price", "supplier_cost", "raw_margin", "aed_price", "usd_price", "stock",
    "quantity", "cn_code", "supplier_code", "commercial_terms", "seller_private_notes",
    "consumer_private_notes", "individual_feedback", "review_text", "comments", "rating", "ugc",
}
SECRET_PATTERNS = {
    "credentialed database URL": re.compile(r"(?:postgres(?:ql)?|mysql)://[^\s/:]+:[^\s@]+@", re.I),
    "likely secret": re.compile(r"(?:api[_-]?key|password|private[_-]?key|access[_-]?token)\s*[:=]\s*[\"']?[A-Za-z0-9_\-/]{8,}", re.I),
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Za-z][A-Za-z ]+\s(?:Street|St|Road|Rd|Avenue|Ave)\b", re.I),
}


def audit_paths(paths: list[Path]) -> list[str]:
    violations = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        header = text.splitlines()[0].casefold().replace(" ", "_") if text else ""
        columns = {part.strip('"') for part in header.split(",")}
        for field in sorted(columns & FORBIDDEN_HEADERS):
            violations.append(f"{path}: forbidden public field {field}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{path}: {label}")
    return violations


def main() -> int:
    violations = audit_paths(PUBLIC_FILES)
    if violations:
        print("FAIL: Maison privacy audit")
        print("\n".join(violations))
        return 1
    print(f"PASS: Maison privacy audit ({len(PUBLIC_FILES)} public files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
