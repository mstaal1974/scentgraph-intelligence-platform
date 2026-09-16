#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path
from aromatwin.services.profile_builder import build_profile_drafts_from_files

INPUT_ROOT = Path("data/imports/supplier-2026-04-26")
OUTPUT = Path("data/profile_drafts.csv")
FIELDS = [
    "id",
    "supplier_item_id",
    "match_candidate_id",
    "candidate_brand",
    "candidate_fragrance_name",
    "likely_original_brand",
    "likely_original_name",
    "profile_title",
    "description_original",
    "description_generation_method",
    "top_notes_json",
    "heart_notes_json",
    "base_notes_json",
    "accords_json",
    "fragrance_family",
    "gender",
    "season_json",
    "occasion_json",
    "mood_json",
    "scent_vector_json",
    "confidence_score",
    "source_confidence",
    "provenance_notes",
    "restricted_content_detected",
    "review_status",
    "reviewer",
    "rejection_reason",
    "approved_at",
    "rejected_at",
    "created_at",
    "updated_at",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build review-only fragrance profile drafts")
    parser.add_argument("--input-root", type=Path, default=INPUT_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    drafts = build_profile_drafts_from_files(
        str(args.input_root / "supplier_items.csv"),
        str(args.input_root / "match_candidates.csv"),
        str(args.input_root / "review_queue.csv"),
        str(args.input_root / "source_provenance.csv"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for identifier, draft in enumerate(drafts, start=1):
            row = draft.model_dump(mode="json")
            row.update(
                {
                    "id": identifier,
                    "reviewer": "",
                    "rejection_reason": "",
                    "approved_at": "",
                    "rejected_at": "",
                    "created_at": "",
                    "updated_at": "",
                }
            )
            for field in (
                "top_notes_json",
                "heart_notes_json",
                "base_notes_json",
                "accords_json",
                "season_json",
                "occasion_json",
                "mood_json",
                "scent_vector_json",
            ):
                row[field] = json.dumps(row[field], separators=(",", ":"))
            writer.writerow(row)
    print(f"Wrote {len(drafts)} needs_human_review profile draft(s) to {args.output}")


if __name__ == "__main__":
    main()
