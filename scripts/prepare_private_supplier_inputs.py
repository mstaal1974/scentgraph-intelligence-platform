#!/usr/bin/env python3
"""Scan private supplier inputs and retain the detailed manifest privately."""

import argparse
import json
from pathlib import Path

from aromatwin.services.private_supplier_intake import PrivateSupplierIntakeService


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/private/imports")
    parser.add_argument("--report", default="data/private/reports/private_supplier_intake.json")
    args = parser.parse_args()
    service = PrivateSupplierIntakeService()
    items = service.scan(args.input)
    report = Path(args.report).resolve()
    private_reports = (Path("data").resolve() / "private" / "reports")
    if not report.is_relative_to(private_reports):
        raise SystemExit("Detailed manifests must be written under data/private/reports/")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps([item.model_dump(mode="json") for item in items], indent=2) + "\n")
    for item in items:
        print(f"{item.supplier_public_label}: {item.readiness_status} ({len(item.blocking_issues)} blockers)")
    return int(any(item.readiness_status.startswith("blocked_") for item in items))


if __name__ == "__main__":
    raise SystemExit(main())
