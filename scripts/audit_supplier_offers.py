#!/usr/bin/env python3
import argparse
import csv
import subprocess
from pathlib import Path

FORBIDDEN = {"code", "cn code", "qty", "aed", "usd", "usd $", "price", "cost", "stock",
             "quantity", "supplier code", "commercial terms"}
SAMPLES = {"supplier_offers_sample.csv", "fatma_supplier_sample.csv"}


def normalise(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def audit(root: Path, tracked: list[str] | None = None) -> list[str]:
    if tracked is None:
        output = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True)
        tracked = [name for name in output.split("\0") if name]
    errors = [f"Private supplier path is tracked: {name}" for name in tracked
              if name.startswith(("data/private/", "private/"))]
    for name in tracked:
        path = root / name
        if path.name not in SAMPLES or not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            exposed = {normalise(header) for header in (reader.fieldnames or [])} & FORBIDDEN
            rows = list(reader)
        if exposed:
            errors.append(f"Public sample exposes private supplier fields: {name}: {sorted(exposed)}")
        if any("fictional" not in normalise(row.get("supplier_name", "")) for row in rows):
            errors.append(f"Public sample supplier names must be explicitly fictional: {name}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = audit(args.root.resolve())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Supplier offer privacy audit passed")


if __name__ == "__main__":
    main()
