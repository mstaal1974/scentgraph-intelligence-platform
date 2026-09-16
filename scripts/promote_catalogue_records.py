"""Promote approved enrichment-review CSV rows into the public catalogue CSV."""

import argparse
import csv
from pathlib import Path

from aromatwin.services.catalogue_promotion import (
    APPROVED_FOR_CATALOGUE,
    CatalogueFragrance,
    promote_enrichment_review,
    write_catalogue_csv,
)


def promote_rows(source_path: Path, output_path: Path) -> tuple[int, int]:
    with source_path.open(newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    catalogue: list[CatalogueFragrance] = []
    accepted = rejected = 0
    for row in rows:
        if row.get("review_status") != APPROVED_FOR_CATALOGUE:
            rejected += 1
            continue
        try:
            record = promote_enrichment_review(row, catalogue)
        except (KeyError, TypeError, ValueError):
            rejected += 1
            continue
        if record not in catalogue:
            catalogue.append(record)
            accepted += 1
    write_catalogue_csv(output_path, catalogue)
    return accepted, rejected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/enrichment_reviews.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/catalogue_fragrances.csv"))
    args = parser.parse_args()
    accepted, rejected = promote_rows(args.input, args.output)
    print(f"Catalogue promotion report: accepted={accepted} rejected={rejected}")


if __name__ == "__main__":
    main()
