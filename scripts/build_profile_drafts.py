#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

from types import SimpleNamespace

from aromatwin.services.profile_builder import build_profile_draft


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


def build_rows(supplier_items_path: Path, match_candidates_path: Path) -> list[dict[str, str]]:
    suppliers = {row["id"]: row for row in _read_rows(supplier_items_path)}
    output: list[dict[str, str]] = []
    for candidate in _read_rows(match_candidates_path):
        supplier_id = candidate["supplier_item_id"]
        if supplier_id not in suppliers:
            raise ValueError(f"Unknown supplier_item_id: {supplier_id}")
        candidate_id = candidate["id"]
        supplier = SimpleNamespace(
            id=int(supplier_id),
            normalised_brand=suppliers[supplier_id].get("normalised_brand", ""),
            normalised_name=suppliers[supplier_id].get("normalised_name", ""),
        )
        candidate_input = SimpleNamespace(
            id=int(candidate_id),
            supplier_item_id=int(supplier_id),
            candidate_brand=candidate["candidate_brand"],
            candidate_fragrance_name=candidate["candidate_fragrance_name"],
            candidate_concentration=candidate.get("candidate_concentration") or None,
            candidate_source_type=candidate["candidate_source_type"],
            candidate_source_reference=candidate.get("candidate_source_reference") or None,
            match_confidence=float(candidate["match_confidence"]),
        )
        draft = build_profile_draft(supplier, candidate_input)
        output.append(
            {
                "supplier_item_id": supplier_id,
                "match_candidate_id": candidate_id,
                "brand": draft.brand,
                "fragrance_name": draft.fragrance_name,
                "concentration": draft.concentration or "",
                "description": draft.description,
                "provenance_notes": draft.provenance_notes,
                "source_type": draft.source_type,
                "source_confidence": str(draft.source_confidence),
                "review_status": draft.review_status,
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build review-only public profile drafts")
    parser.add_argument("--supplier-items", type=Path, default=Path("data/supplier_items.csv"))
    parser.add_argument("--match-candidates", type=Path, default=Path("data/match_candidates.csv"))
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
