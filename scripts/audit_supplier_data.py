#!/usr/bin/env python3
import argparse
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
    return [root / item for item in output.split("\0") if item]


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    sample = root / "data/samples/supplier_identity_sample.csv"
    try:
        validate_public_supplier_sample(sample)
    except (OSError, ValueError) as error:
        errors.append(str(error))

    forbidden = {normalise_column(column) for column in FORBIDDEN_PUBLIC_SAMPLE_COLUMNS}
    for path in tracked_files(root):
        relative = path.relative_to(root).as_posix()
        if relative.startswith(("data/private/", "private/")):
            errors.append(f"Private supplier path is tracked: {relative}")
        if relative.startswith("data/imports/") and path.suffix.casefold() in {".xls", ".xlsx"}:
            errors.append(f"Raw supplier spreadsheet is tracked: {relative}")
        if relative.startswith("data/imports/") and path.suffix.casefold() == ".csv":
            with path.open(encoding="utf-8-sig") as handle:
                headers = {normalise_column(value) for value in handle.readline().split(",")}
            exposed = headers & forbidden
            if exposed:
                errors.append(
                    f"Tracked staging export exposes sensitive columns: {relative}: {sorted(exposed)}"
                )
        if relative.startswith("data/samples/") and path.suffix.casefold() == ".csv":
            with path.open(encoding="utf-8-sig") as handle:
                headers = {normalise_column(value) for value in handle.readline().split(",")}
            exposed = headers & forbidden
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
