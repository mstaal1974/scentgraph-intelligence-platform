#!/usr/bin/env python3
"""Build safe, review-only enrichment CSV records from profile drafts."""

import argparse
import csv
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.services.enrichment_review import (
    EnrichmentSource,
    build_enrichment_review,
    load_profile_drafts,
)

OUTPUT_FIELDS = (
    "id",
    "profile_draft_id",
    "brand",
    "fragrance_name",
    "concentration",
    "description_original",
    "provenance_summary",
    "source_ids",
    "source_confidence",
    "licensing_risk",
    "copied_restricted_content",
    "review_status",
    "reviewer",
    "rejection_reason",
)


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def _read_sources(path: Path | None) -> dict[int, list[EnrichmentSource]]:
    grouped: dict[int, list[EnrichmentSource]] = {}
    if path is None or not path.exists():
        return grouped
    with path.open(newline="", encoding="utf-8-sig") as source_file:
        for row in csv.DictReader(source_file):
            draft_id = int(row["profile_draft_id"])
            grouped.setdefault(draft_id, []).append(
                EnrichmentSource(
                    id=int(row["id"]),
                    source_name=row["source_name"],
                    source_type=row["source_type"],
                    source_reference=row["source_reference"],
                    source_url=row.get("source_url") or None,
                    licence_status=row["licence_status"],
                    commercial_use_allowed=_as_bool(row["commercial_use_allowed"]),
                    source_confidence=float(row["source_confidence"]),
                    licensing_risk=row["licensing_risk"],
                    reference_only=_as_bool(row.get("reference_only", "false")),
                )
            )
    return grouped


def build_rows(
    profile_drafts_path: Path, enrichment_sources_path: Path | None = None
) -> list[dict[str, str]]:
    sources_by_draft = _read_sources(enrichment_sources_path)
    output: list[dict[str, str]] = []
    for position, row in enumerate(load_profile_drafts(profile_drafts_path), start=1):
        draft_id = int(row.get("id") or position)
        draft = SimpleNamespace(
            id=draft_id,
            brand=row["brand"],
            fragrance_name=row["fragrance_name"],
            concentration=row.get("concentration") or None,
            review_status=row["review_status"],
        )
        review = build_enrichment_review(
            draft, sources_by_draft.get(draft_id, []), enrichment_review_id=position
        )
        output.append(
            {
                "id": str(review.id),
                "profile_draft_id": str(review.profile_draft_id),
                "brand": review.brand,
                "fragrance_name": review.fragrance_name,
                "concentration": review.concentration or "",
                "description_original": review.description_original,
                "provenance_summary": review.provenance_summary,
                "source_ids": "|".join(str(value) for value in review.source_ids),
                "source_confidence": str(review.source_confidence),
                "licensing_risk": review.licensing_risk,
                "copied_restricted_content": "false",
                "review_status": review.review_status,
                "reviewer": "",
                "rejection_reason": "",
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build independent enrichment review records")
    parser.add_argument("--profile-drafts", type=Path, default=Path("data/profile_drafts.csv"))
    parser.add_argument(
        "--enrichment-sources", type=Path, default=Path("data/enrichment_sources.csv")
    )
    parser.add_argument("--output", type=Path, default=Path("data/enrichment_reviews.csv"))
    args = parser.parse_args()
    rows = build_rows(args.profile_drafts, args.enrichment_sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
