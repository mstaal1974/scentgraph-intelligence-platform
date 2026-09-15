#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

EXPECTED = {
    "brands.csv": {"id", "name", "slug", "verified"},
    "fragrances.csv": {"id", "brand_id", "name", "slug", "source_confidence"},
    "notes.csv": {"id", "name", "slug", "note_type"},
    "accords.csv": {"id", "name", "slug"},
    "fragrance_notes.csv": {"fragrance_id", "note_id", "pyramid_level"},
    "fragrance_accords.csv": {"fragrance_id", "accord_id", "weight"},
    "scent_vectors.csv": {"fragrance_id", "warm", "fresh", "sweet", "longevity"},
    "clone_relationships.csv": {"id", "clone_fragrance_id", "original_fragrance_id"},
    "products.csv": {"id", "fragrance_id", "sku"},
    "aliases.csv": {"id", "entity_type", "entity_id", "alias"},
    "source_provenance.csv": {"id", "entity_type", "entity_id", "source_name", "confidence"},
}


def validate(directory: Path) -> list[str]:
    errors = []
    for name, required in EXPECTED.items():
        path = directory / name
        if not path.exists():
            errors.append(f"{name}: missing file")
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            headers = set(next(csv.reader(handle), []))
        missing = required - headers
        if missing:
            errors.append(f"{name}: missing headers {', '.join(sorted(missing))}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    errors = validate(args.directory)
    if errors:
        raise SystemExit("\n".join(errors))
    print("CSV templates valid")


if __name__ == "__main__":
    main()
