#!/usr/bin/env python3
"""Fail closed on privacy or commercial leakage in Scentprint public artifacts."""

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aromatwin.services.scentprint_quiz_contracts import (  # noqa: E402
    get_quiz_contract,
    validate_quiz_contract,
)

FORBIDDEN_HEADERS = {
    "name", "email", "phone", "address", "age", "gender", "ethnicity", "health",
    "medical", "biometric", "supplier_price", "supplier_cost", "supplier_code", "cn_code",
    "aed", "usd", "cost", "margin", "stock", "quantity", "commercial_terms",
    "seller_private_notes", "consumer_private_notes", "raw_feedback", "password", "token",
    "api_key", "database_url",
}
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")
SECRET = re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|postgres(?:ql)?://[^\s:/]+:[^\s@]+@)", re.I)


def audit_paths(paths: list[Path], contract: dict[str, object] | None = None) -> list[str]:
    errors = validate_quiz_contract(contract or get_quiz_contract())
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig")
        if EMAIL.search(text) or PHONE.search(text) or SECRET.search(text):
            errors.append(f"{path}: apparent contact data or secret")
        if path.suffix.casefold() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                header = next(csv.reader(handle), [])
            normalized = {item.strip().casefold().replace(" ", "_") for item in header}
            leaked = sorted(normalized & FORBIDDEN_HEADERS)
            if leaked:
                errors.append(f"{path}: forbidden public fields {leaked}")
            if "answer_type" in normalized and re.search(r",\s*free_text\s*,", f",{text},", re.I):
                errors.append(f"{path}: open-ended free text enabled")
    return errors


def default_paths(root: Path) -> list[Path]:
    samples = sorted((root / "data/samples").glob("scentprint_quiz*"))
    docs = [root / "docs/scentprint-quiz-contract.md", root / "docs/consumer-scent-intelligence.md",
            root / "docs/maison-integration-readiness.md", root / "docs/api-contract.md",
            root / "docs/roadmap.md"]
    return samples + docs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    paths = args.paths or default_paths(args.root)
    errors = audit_paths(paths)
    if errors:
        print("Scentprint quiz privacy audit failed:\n- " + "\n- ".join(errors))
        return 1
    print(f"Scentprint quiz privacy audit passed ({len(paths)} public artifacts scanned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
