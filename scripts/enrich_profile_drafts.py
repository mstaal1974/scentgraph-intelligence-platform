#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path
from aromatwin.services.enrichment import generate_enrichment_review

REVIEW_FIELDS = [
    "id",
    "profile_draft_id",
    "approved_brand",
    "approved_fragrance_name",
    "official_source_url",
    "source_summary",
    "description_original",
    "note_pyramid_json",
    "accords_json",
    "family",
    "gender",
    "season_json",
    "occasion_json",
    "mood_json",
    "scent_vector_json",
    "enrichment_confidence",
    "licensing_risk",
    "copied_text_detected",
    "review_status",
    "reviewer",
    "review_notes",
    "approved_at",
    "rejected_at",
    "created_at",
    "updated_at",
]


def read_csv(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in (
            "commercial_use_allowed",
            "can_copy_text",
            "can_copy_images",
            "can_use_for_factual_reference",
            "can_use_for_matching",
        ):
            row[key] = str(row.get(key, "")).casefold() == "true"
        if row.get("source_confidence") not in (None, ""):
            row["source_confidence"] = float(row["source_confidence"])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate original, review-only fragrance enrichments"
    )
    parser.add_argument("--profiles", type=Path, default=Path("data/profile_drafts.csv"))
    parser.add_argument("--sources", type=Path, default=Path("data/enrichment_sources.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/enrichment_reviews.csv"))
    parser.add_argument(
        "--report", type=Path, default=Path("data/enrichment_validation_report.csv")
    )
    args = parser.parse_args()
    profiles = read_csv(args.profiles)
    sources = read_csv(args.sources)
    reviews = []
    report = []
    for profile in profiles:
        try:
            review = generate_enrichment_review(profile, sources)
            row = review.model_dump(mode="json")
            row.update(
                {
                    "id": len(reviews) + 1,
                    "reviewer": "",
                    "review_notes": "",
                    "approved_at": "",
                    "rejected_at": "",
                    "created_at": "",
                    "updated_at": "",
                }
            )
            for field in (
                "note_pyramid_json",
                "accords_json",
                "season_json",
                "occasion_json",
                "mood_json",
                "scent_vector_json",
            ):
                row[field] = json.dumps(row[field], separators=(",", ":"))
            reviews.append(row)
            report.append({"profile_draft_id": profile["id"], "status": "valid", "error": ""})
        except (KeyError, TypeError, ValueError) as error:
            report.append(
                {
                    "profile_draft_id": profile.get("id", ""),
                    "status": "invalid",
                    "error": str(error),
                }
            )
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(reviews)
    with args.report.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["profile_draft_id", "status", "error"])
        writer.writeheader()
        writer.writerows(report)
    print(f"Wrote {len(reviews)} needs_human_review enrichment record(s)")


if __name__ == "__main__":
    main()
