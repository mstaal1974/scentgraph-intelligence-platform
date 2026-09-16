#!/usr/bin/env python3
"""Promote approved enrichment-review CSV rows into the public catalogue CSV."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.services.catalogue_promotion import (
    CatalogueFragrance,
    load_approved_enrichment_reviews,
    promote_enrichment_review,
    write_catalogue_csv,
)


def promote_rows(
    source_path: Path,
    output_path: Path,
    *,
    confidence_threshold: float = 0.75,
) -> tuple[int, int]:
    rows = load_approved_enrichment_reviews(source_path)
    with source_path.open(newline="", encoding="utf-8-sig") as source:
        total_rows = max(sum(1 for _ in source) - 1, 0)
    catalogue: list[CatalogueFragrance] = []
    accepted = 0
    rejected = total_rows - len(rows)
    for row in rows:
        try:
            record = promote_enrichment_review(
                row, catalogue, confidence_threshold=confidence_threshold
            )
        except (KeyError, TypeError, ValueError):
            rejected += 1
            continue
        if record not in catalogue:
            catalogue.append(record)
            accepted += 1
        else:
            # An idempotent repeat is safe, but is not a newly accepted catalogue row.
            rejected += 1
    write_catalogue_csv(output_path, catalogue)
    return accepted, rejected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/enrichment_reviews.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/catalogue_fragrances.csv"))
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.75,
        help="Minimum source confidence required for promotion (default: 0.75)",
    )
    args = parser.parse_args()
    accepted, rejected = promote_rows(
        args.input, args.output, confidence_threshold=args.confidence_threshold
    )
    print(f"Catalogue promotion report: accepted={accepted} rejected={rejected}")


if __name__ == "__main__":
    main()
