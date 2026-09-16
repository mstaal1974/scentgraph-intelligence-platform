#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from aromatwin.services.supplier_importer import (
    SupplierBatchValidationError,
    prepare_supplier_directory,
    prepare_supplier_file,
)

DEFAULT_IMPORT = Path("data/imports/supplier-2026-04-26")


def serialise(value: object) -> object:
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    raise TypeError(f"Cannot serialise {type(value)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate supplier source files and create non-catalogue staging output"
    )
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_IMPORT)
    parser.add_argument("--supplier-name", required=True)
    parser.add_argument("--output", type=Path, default=Path("supplier-staging.json"))
    parser.add_argument("--report", type=Path, default=Path("validation-report.json"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = (
            prepare_supplier_directory(args.input, args.supplier_name)
            if args.input.is_dir()
            else prepare_supplier_file(args.input, args.supplier_name)
        )
    except SupplierBatchValidationError as error:
        args.report.write_text(json.dumps(error.report, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(f"Supplier validation failed; see {args.report}") from error
    args.output.write_text(
        json.dumps([asdict(row) for row in result.rows], default=serialise, indent=2) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(json.dumps(result.report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Staged {len(result.rows)} supplier rows as supplier_imported; "
        "catalogue promotion remains disabled."
    )


if __name__ == "__main__":
    main()
