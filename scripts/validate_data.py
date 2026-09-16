#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

EXPECTED = {
    "samples/supplier_identity_sample.csv": {"BRAND", "NAME", "ORI"},
    "reference_match_template.csv": {
        "supplier_item_id",
        "candidate_source_type",
        "review_status",
        "commercial_use_allowed",
        "can_copy_text",
        "can_copy_images",
        "can_use_for_matching",
    },
    "enrichment_review_template.csv": {
        "match_candidate_id",
        "official_source_url",
        "description_original",
        "review_status",
        "source_confidence",
    },
    "review_statuses.csv": {"code", "description", "terminal"},
    "brands.csv": {"id", "name", "review_status"},
    "fragrances.csv": {"id", "enrichment_review_id", "name", "review_status"},
    "notes.csv": {"id", "name", "slug", "note_type"},
    "accords.csv": {"id", "name", "slug"},
    "fragrance_notes.csv": {"fragrance_id", "note_id", "pyramid_level"},
    "fragrance_accords.csv": {"fragrance_id", "accord_id", "weight"},
    "scent_vectors.csv": {"fragrance_id", "warm", "fresh", "longevity"},
    "clone_relationships.csv": {"id", "supplier_item_id", "score_status", "review_status"},
    "products.csv": {"id", "supplier_item_id", "sku"},
    "aliases.csv": {"id", "entity_type", "entity_id", "alias"},
    "source_provenance.csv": {
        "id",
        "entity_type",
        "entity_id",
        "licence_status",
        "commercial_use_allowed",
        "confidence",
    },
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
