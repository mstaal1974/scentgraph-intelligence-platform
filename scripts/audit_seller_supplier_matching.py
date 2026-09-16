#!/usr/bin/env python3
"""Fail closed when tracked demand artifacts cross privacy boundaries."""

import argparse
import csv
import subprocess
from pathlib import Path

SAMPLES = {"seller_demand_briefs_sample.csv", "seller_supplier_matches_sample.csv",
           "supplier_opportunity_summary_sample.csv"}
FORBIDDEN = {"seller name", "private seller notes", "supplier name", "supplier price",
             "supplier cost", "supplier code", "cn code", "quantity", "stock", "aed price",
             "usd price", "margin", "commercial terms"}
FORBIDDEN_PARTS = ("private seller", "supplier price", "supplier cost", "supplier code",
                   "cn code", "quantity", "stock", "aed", "usd", "commercial term")


def normalise(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def audit(root: Path, tracked: list[str] | None = None) -> list[str]:
    if tracked is None:
        output = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True)
        tracked = [value for value in output.split("\0") if value]
    errors = [f"Private operational artifact is tracked: {name}" for name in tracked
              if name.startswith(("data/private/", "private/"))]
    for name in tracked:
        path = root / name
        if path.name not in SAMPLES or not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            headers = {normalise(value) for value in (csv.DictReader(handle).fieldnames or [])}
        leaked = {header for header in headers
                  if header in FORBIDDEN or any(marker in header for marker in FORBIDDEN_PARTS)}
        if leaked:
            errors.append(f"Public demand sample exposes private fields: {name}: {sorted(leaked)}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = audit(args.root.resolve())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Seller/supplier matching privacy audit passed")


if __name__ == "__main__":
    main()
