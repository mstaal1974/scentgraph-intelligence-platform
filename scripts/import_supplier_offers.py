#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from aromatwin.services.supplier_offer_importer import (
    prepare_supplier_offer_file,
    write_private_staging,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage a private supplier offer price list")
    parser.add_argument("input", type=Path)
    parser.add_argument("--supplier-name", required=True)
    parser.add_argument("--supplier-format", choices=["auto", "existing_supplier", "fatma"], default="auto")
    parser.add_argument("--staging-dir", type=Path, default=Path("data/private/staging/supplier_offers"))
    parser.add_argument("--report-dir", type=Path, default=Path("data/private/reports"))
    args = parser.parse_args()
    result = prepare_supplier_offer_file(args.input, args.supplier_name, args.supplier_format)
    stem = result.report["source_sha256"][:12]
    staging = args.staging_dir / f"offers-{stem}.json"
    report = args.report_dir / f"supplier-offer-import-{stem}.json"
    write_private_staging(result, staging)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result.report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result.report["rows"], "duplicate_rows": result.report["duplicate_rows"],
                      "warnings": result.report["warnings"], "report": report.as_posix()}))


if __name__ == "__main__":
    main()
