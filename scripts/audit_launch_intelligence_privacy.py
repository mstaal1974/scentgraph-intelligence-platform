#!/usr/bin/env python3
"""Fail closed on confidential launch fields in tracked public launch artifacts."""
import argparse
import csv
import re
import subprocess
from pathlib import Path

FORBIDDEN_HEADERS = {"supplier price", "supplier cost", "supplier code", "cn code", "stock", "quantity",
                     "aed price", "usd price", "cost", "raw margin", "commercial terms", "seller private notes",
                     "consumer private notes", "email", "phone", "address", "raw individual feedback"}
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")


def normalise(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())


def audit(root: Path, tracked: list[str] | None = None) -> list[str]:
    if tracked is None:
        output = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True)
        tracked = [name for name in output.split("\0") if name]
    errors = [f"Detailed launch output is tracked outside its private boundary: {name}" for name in tracked
              if "launch" in name.casefold() and name.startswith("data/") and
              not name.startswith(("data/private/", "data/samples/"))]
    for name in tracked:
        path = root / name
        if not name.startswith("data/samples/launch_") or path.suffix.casefold() != ".csv" or not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        headers = {normalise(value) for value in (rows[0] if rows else [])}
        leaked = sorted(headers & FORBIDDEN_HEADERS)
        if leaked:
            errors.append(f"Public launch sample exposes forbidden fields: {name}: {leaked}")
        content = "\n".join(",".join(row) for row in rows[1:])
        if EMAIL.search(content) or PHONE.search(content):
            errors.append(f"Public launch sample contains apparent contact data: {name}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = audit(args.root.resolve())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Launch intelligence privacy audit passed")

if __name__ == "__main__":
    main()
