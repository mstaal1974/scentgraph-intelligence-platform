#!/usr/bin/env python3
"""Reject secret-like values and private/commercial columns in packaging public files."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = [ROOT / "data/samples/commercial_plan_catalogue_sample.csv",
           ROOT / "data/samples/api_entitlement_matrix_sample.csv",
           ROOT / "data/samples/tenant_feature_access_sample.csv",
           ROOT / "data/samples/commercial_readiness_sample.csv"]
DOCS = [ROOT / "docs/commercial-packaging-api-entitlements.md"]
VALUE_PATTERNS = {
    "credential URL": re.compile(r"(?:postgres|mysql|mongodb)://[^\s/:]+:[^\s/@]+@", re.I),
    "likely secret": re.compile(r"(?:sk_live_|sk_test_|AKIA)[A-Za-z0-9_-]{12,}", re.I),
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?:\+\d{1,3}[ -]?)?\d{3}[ -]\d{3}[ -]\d{4}"),
    "street address": re.compile(r"\b\d{1,5}\s+[A-Za-z]+\s+(?:Street|Road|Avenue|Lane)\b", re.I),
}
FORBIDDEN_HEADERS = {"supplier_price", "supplier_cost", "supplier_code", "cn_code", "stock",
                     "quantity", "aed_price", "usd_price", "raw_margin", "commercial_terms",
                     "seller_private_notes", "consumer_private_notes", "api_key", "password",
                     "customer_id", "tenant_id"}


def audit(paths: list[Path] | None = None) -> list[str]:
    violations = []
    targets = paths or SAMPLES + DOCS
    for path in targets:
        if not path.is_file():
            violations.append(f"missing required public file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in VALUE_PATTERNS.items():
            if pattern.search(text):
                violations.append(f"{path.name}: {label}")
        if path.suffix == ".csv":
            headers = {h.strip().lower() for h in text.splitlines()[0].split(",")}
            for header in sorted(headers & FORBIDDEN_HEADERS):
                violations.append(f"{path.name}: forbidden column {header}")
            if re.search(r"\b(?:customer|tenant)_[0-9a-f]{8,}\b", text, re.I):
                violations.append(f"{path.name}: likely real customer or tenant identifier")
    return violations


def main() -> int:
    violations = audit()
    if violations:
        for violation in violations:
            print(f"FAIL: {violation}", file=sys.stderr)
        return 1
    print(f"PASS: commercial packaging privacy audit ({len(SAMPLES) + len(DOCS)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
