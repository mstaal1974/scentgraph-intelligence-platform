#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

from aromatwin.services.profile_builder import NEEDS_HUMAN_REVIEW


OUTPUT_FIELDS = (
    "supplier_item_id",
    "match_candidate_id",
    "brand",
    "fragrance_name",
    "concentration",
    "description",
    "provenance_notes",
    "source_type",
    "source_confidence",
    "review_status",
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def build_rows(
    supplier_items_path: Path, match_candidates_path: Path
) -> list[dict[str, str]]:
    suppliers = {row["id"]: row for row in _read_rows(supplier_items_path)}
    output: list[dict[str, str]] = []
    for candidate in _read_rows(match_candidates_path):
        supplier_id = candidate["supplier_item_id"]
        if supplier_id not in suppliers:
            raise ValueError(f"Unknown supplier_item_id: {supplier_id}")
        candidate_id = candidate["id"]
        brand = candidate["candidate_brand"].strip()
        name = candidate["candidate_fragrance_name"].strip()
        source_type = candidate["candidate_source_type"].strip()
        output.append(
            {
                "supplier_item_id": supplier_id,
                "match_candidate_id": candidate_id,
                "brand": brand,
                "fragrance_name": name,
                "concentration": candidate.get("candidate_concentration", "").strip(),
                "description": (
                    f"Draft profile for {brand} {name}. Original descriptive details must be "
                    "written and verified by a human reviewer."
                ),
                "provenance_notes": (
                    f"Identity proposed by {source_type} candidate {candidate_id} from supplier "
                    f"item {supplier_id}; descriptive fields were not copied."
                ),
                "source_type": source_type,
                "source_confidence": candidate["match_confidence"],
                "review_status": NEEDS_HUMAN_REVIEW,
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build review-only public profile drafts")
    parser.add_argument("--supplier-items", type=Path, default=Path("data/supplier_items.csv"))
    parser.add_argument(
        "--match-candidates", type=Path, default=Path("data/match_candidates.csv")
    )
    parser.add_argument("--output", type=Path, default=Path("data/profile_drafts.csv"))
    args = parser.parse_args()

    rows = build_rows(args.supplier_items, args.match_candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

