#!/usr/bin/env python3
"""Build review-only drafts from private staged offers; never publishes catalogue data."""
from __future__ import annotations

import argparse
from pathlib import Path

from aromatwin.services.bulk_profile_generation import (
    generate_bulk_profile_drafts,
    load_records,
    write_private_drafts,
)

PRIVATE_OFFERS = Path("data/private/staging/supplier_offers")
DEFAULT_OUTPUT = Path("data/private/staging/profile_drafts/bulk_profile_drafts.json")


def read_directory(directory: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    if directory.exists():
        for path in sorted(directory.iterdir()):
            if path.suffix.casefold() in {".json", ".csv"}:
                records.extend(load_records(path))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offers-dir", type=Path, default=PRIVATE_OFFERS)
    parser.add_argument("--matches", type=Path)
    parser.add_argument("--existing-drafts", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    offers = read_directory(args.offers_dir)
    matches = load_records(args.matches) if args.matches and args.matches.exists() else []
    existing = load_records(args.existing_drafts) if args.existing_drafts and args.existing_drafts.exists() else []
    result = generate_bulk_profile_drafts(offers, matches, existing)
    write_private_drafts(result.drafts, args.output)
    print(f"accepted={result.accepted_count} rejected={result.rejected_count}")
    print(f"unique_fragrance_candidates={result.unique_candidate_count}")
    print(f"profile_drafts_created={len(result.drafts)}")
    print(f"skipped_as_duplicates={result.skipped_duplicate_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
