#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from scentgraph.services.importer import prepare_supplier_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a supplier CSV for curator review")
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--output", type=Path, default=Path("staging.csv"))
    parser.add_argument("--report", type=Path, default=Path("validation-report.json"))
    args = parser.parse_args()
    result = prepare_supplier_csv(args.input, args.source_name)
    result.staging.to_csv(args.output, index=False)
    args.report.write_text(json.dumps(result.report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
