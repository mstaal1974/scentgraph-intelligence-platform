#!/usr/bin/env python3
import argparse
import csv
import subprocess
from pathlib import Path

from aromatwin.services.supplier_privacy import (
    FORBIDDEN_PUBLIC_SAMPLE_COLUMNS,
    normalise_column,
    validate_public_supplier_sample,
)


def tracked_files(root: Path) -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root, text=True, encoding="utf-8"
    )
    return [root / item for item in output.split("\0") if item and (root / item).is_file()]


def exposed_sample_columns(relative: str, headers: set[str]) -> set[str]:
    """Return private supplier columns, allowing SKU only in the product-variant sample."""
    forbidden = {normalise_column(column) for column in FORBIDDEN_PUBLIC_SAMPLE_COLUMNS}
    exposed = {normalise_column(header) for header in headers} & forbidden
    if relative == "data/samples/product_variants_sample.csv":
        exposed.discard(normalise_column("SKU"))
    return exposed


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    sample = root / "data/samples/supplier_identity_sample.csv"
    try:
        validate_public_supplier_sample(sample)
    except (OSError, ValueError) as error:
        errors.append(str(error))

    for path in tracked_files(root):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(("data/private/", "private/")):
            errors.append(f"Private supplier path is tracked: {relative}")
        if relative.startswith("data/imports/") and path.suffix.casefold() in {
            ".csv",
            ".xls",
            ".xlsx",
        }:
            errors.append(f"Raw supplier import is tracked: {relative}")
        if relative.startswith("data/samples/") and path.suffix.casefold() in {".xls", ".xlsx"}:
            errors.append(f"Tracked spreadsheet is not allowed in public samples: {relative}")
        if relative.startswith("data/samples/") and path.suffix.casefold() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as handle:
                headers = {normalise_column(value) for value in next(csv.reader(handle), [])}
            exposed = exposed_sample_columns(relative, headers)
            if exposed:
                errors.append(
                    f"Public sample exposes sensitive columns: {relative}: {sorted(exposed)}"
                )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit tracked supplier data for public exposure")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = audit(args.root.resolve())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Supplier data privacy audit passed")


if __name__ == "__main__":
    main()
