#!/usr/bin/env python3
"""Fail closed when tracked public data contains consumer or commercial leakage."""

import argparse
import csv
import re
import subprocess
from pathlib import Path

FORBIDDEN_PARTS = (
    "email", "phone", "address", "private note", "free text private note", "contact detail",
    "full name", "raw feedback note", "seller private", "supplier price", "supplier cost",
    "supplier code", "cn code", "stock", "quantity", "aed", "usd", "cost", "margin",
    "commercial term",
)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)")


def normalise(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())


def audit(root: Path, tracked: list[str] | None = None) -> list[str]:
    if tracked is None:
        output = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True)
        tracked = [name for name in output.split("\0") if name]
    errors = [f"Private consumer artifact is tracked: {name}" for name in tracked
              if name.startswith(("data/private/", "private/"))]
    for name in tracked:
        path = root / name
        if not name.startswith("data/samples/") or path.suffix.casefold() != ".csv" or not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        headers = [normalise(value) for value in (rows[0] if rows else [])]
        leaked = sorted({header for header in headers
                         if any(marker in header for marker in FORBIDDEN_PARTS)})
        if leaked:
            errors.append(f"Public sample exposes forbidden fields: {name}: {leaked}")
        content = "\n".join(",".join(row) for row in rows[1:])
        if EMAIL.search(content) or PHONE.search(content):
            errors.append(f"Public sample contains apparent contact data: {name}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = audit(args.root.resolve())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Consumer scent privacy audit passed")


if __name__ == "__main__":
    main()
