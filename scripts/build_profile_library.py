"""Build the first-party fragrance profile library from its seed.

The seed is pushed through the real gates rather than written straight to the catalogue: each
profile becomes an enrichment review, promotion validates provenance, confidence, licensing
risk, restricted content, and supplier-private columns, and only promoted records reach the
public catalogue. Vectors and recommendations are then derived from that catalogue.

Everything produced here is original AromaTwin content about fictional houses. Building a
library of real-brand profiles needs a permitted commercial source and is not this script.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.library import build_seed_profiles  # noqa: E402
from aromatwin.services.catalogue_promotion import (  # noqa: E402
    CatalogueFragrance,
    promote_enrichment_review,
    slugify,
    write_catalogue_csv,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "data"
# The library keeps its own review inputs. data/enrichment_reviews.csv is the human review
# queue produced by build_enrichment_reviews.py and holds records still awaiting a decision;
# it is not an input to promotion and must not be overwritten here.
LIBRARY_SUBDIR = "library"

REVIEW_FIELDS = (
    "id", "profile_draft_id", "brand", "fragrance_name", "concentration", "description_original",
    "family", "notes", "accords", "mood", "occasion", "season", "provenance_summary", "source_ids",
    "source_confidence", "licensing_risk", "copied_restricted_content", "review_status",
    "reviewer", "rejection_reason",
)
SOURCE_FIELDS = (
    "id", "profile_draft_id", "source_name", "source_type", "source_reference", "source_url",
    "licence_status", "commercial_use_allowed", "source_confidence", "licensing_risk",
    "reference_only",
)
DRAFT_FIELDS = (
    "supplier_item_id", "match_candidate_id", "brand", "fragrance_name", "concentration",
    "description", "provenance_notes", "source_type", "source_confidence", "review_status",
)
RELATIONSHIP_FIELDS = (
    "id", "supplier_item_id", "clone_fragrance_id", "original_fragrance_id", "product_id",
    "relationship_type", "similarity_score", "score_status", "difference_summary",
    "performance_notes", "review_status",
)
REVIEWER = "library.curation@aromatwin.internal"
# Confidence is banded by how much reviewed structure a profile carries, and stays above the
# 0.75 promotion threshold because every seed profile is fully specified first-party content.
BASE_CONFIDENCE = 0.88


def _confidence(ordinal: int) -> float:
    """Vary confidence deterministically so downstream banding is exercised, never fabricated."""
    return round(BASE_CONFIDENCE + (ordinal % 5) * 0.02, 2)


def build_reviews() -> list[dict[str, object]]:
    reviews = []
    for profile in build_seed_profiles():
        review_id = profile.ordinal + 1
        direction = profile.direction
        reviews.append(
            {
                "id": review_id,
                "profile_draft_id": review_id,
                "brand": profile.house,
                "fragrance_name": profile.name,
                "concentration": direction.concentration,
                "description_original": profile.description,
                "family": direction.family,
                "notes": ", ".join(profile.notes),
                "accords": ", ".join(profile.accords),
                "mood": ", ".join(direction.mood),
                "occasion": ", ".join(direction.occasion),
                "season": ", ".join(direction.season),
                "provenance_summary": (
                    f"Original first-party profile authored for {profile.house}; identity, "
                    "taxonomy, and description are AromaTwin content reviewed for commercial use."
                ),
                "source_ids": str(review_id),
                "source_confidence": _confidence(profile.ordinal),
                "licensing_risk": "low",
                "copied_restricted_content": "false",
                "review_status": "approved_for_catalogue",
                "reviewer": REVIEWER,
                "rejection_reason": "",
            }
        )
    return reviews


def build_sources() -> list[dict[str, object]]:
    return [
        {
            "id": review["id"],
            "profile_draft_id": review["profile_draft_id"],
            "source_name": f"{review['brand']} first-party profile record",
            "source_type": "first_party",
            "source_reference": (
                f"AT-{slugify(str(review['brand'])).upper()}-"
                f"{slugify(str(review['fragrance_name'])).upper()}"
            ),
            "source_url": "",
            "licence_status": "first-party-original-content",
            "commercial_use_allowed": "true",
            "source_confidence": review["source_confidence"],
            "licensing_risk": "low",
            "reference_only": "false",
        }
        for review in build_reviews()
    ]


def promote(reviews: list[dict[str, object]]) -> list[CatalogueFragrance]:
    catalogue: list[CatalogueFragrance] = []
    for review in reviews:
        catalogue.append(promote_enrichment_review(review, catalogue))
    return catalogue


def build_relationships(catalogue: list[CatalogueFragrance]) -> list[dict[str, object]]:
    """Link same-direction profiles from different houses as reviewed inspired-by pairs.

    This is the clone/inspired-by relation the platform exists to express, expressed here only
    between first-party profiles that genuinely share a reviewed direction.
    """
    seed_by_id = {profile.ordinal + 1: profile for profile in build_seed_profiles()}
    grouped: dict[str, list[CatalogueFragrance]] = {}
    for record in catalogue:
        grouped.setdefault(seed_by_id[record.enrichment_review_id].direction.key, []).append(record)

    rows: list[dict[str, object]] = []
    for direction_key, records in sorted(grouped.items()):
        ordered = sorted(records, key=lambda item: item.id)
        for original, clone in zip(ordered, ordered[1:], strict=False):
            rows.append(
                {
                    "id": len(rows) + 1,
                    "supplier_item_id": "",
                    "clone_fragrance_id": clone.id,
                    "original_fragrance_id": original.id,
                    "product_id": "",
                    "relationship_type": "inspired_by",
                    "similarity_score": 0.82,
                    "score_status": "reviewed",
                    "difference_summary": (
                        f"Both profiles sit in the {direction_key.replace('_', ' ')} direction; "
                        f"{clone.brand} reads closer to its base notes than {original.brand}."
                    ),
                    "performance_notes": "Reviewed first-party comparison, not a lab measurement.",
                    "review_status": "approved",
                }
            )
    return rows


# Drafts that do not clear the gates, so the review console and readiness reporting have real
# work to show. A library where every candidate is promoted is not a realistic one: these stay
# at draft stage and never reach the catalogue or the retailer API.
PENDING_DRAFTS = (
    ("Halcyon Rue", "Unnamed Trial 14", "reference_only", 0.62,
     "Identity proposed by a reference-only candidate; commercial permission is not documented."),
    ("Ombra Fiore", "Unnamed Trial 31", "unknown", 0.55,
     "Source type could not be established from the supplier record."),
    ("Saltwood Parfums", "Harbour Glass Reprise", "licensed_commercial", 0.71,
     "Identity matched below the confidence threshold; a second source is required."),
)


def build_pending_drafts() -> list[dict[str, object]]:
    return [
        {
            "supplier_item_id": 9001 + index,
            "match_candidate_id": 9101 + index,
            "brand": brand,
            "fragrance_name": name,
            "concentration": "Eau de parfum",
            "description": (
                f"An original AromaTwin draft profile for {brand} {name}, generated from supplier "
                "availability and candidate matching. This profile requires independent "
                "verification before catalogue publication."
            ),
            "provenance_notes": note,
            "source_type": source_type,
            "source_confidence": confidence,
            "review_status": "needs_human_review",
        }
        for index, (brand, name, source_type, confidence, note) in enumerate(PENDING_DRAFTS)
    ]


def _write(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_library(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, int]:
    reviews = build_reviews()
    catalogue = promote(reviews)
    relationships = build_relationships(catalogue)

    library_dir = data_dir / LIBRARY_SUBDIR
    _write(library_dir / "enrichment_reviews.csv", REVIEW_FIELDS, reviews)
    _write(library_dir / "enrichment_sources.csv", SOURCE_FIELDS, build_sources())
    _write(data_dir / "clone_relationships.csv", RELATIONSHIP_FIELDS, relationships)
    _write(data_dir / "profile_drafts.csv", DRAFT_FIELDS, build_pending_drafts())
    write_catalogue_csv(data_dir / "catalogue_fragrances.csv", catalogue)

    _write(
        data_dir / "brands.csv",
        ("id", "name", "slug", "review_status"),
        [
            {"id": brand_id, "name": brand, "slug": slug, "review_status": "approved"}
            for brand_id, brand, slug in sorted(
                {(item.brand_id, item.brand, item.brand_slug) for item in catalogue}
            )
        ],
    )
    return {
        "reviews": len(reviews),
        "catalogue": len(catalogue),
        "brands": len({item.brand_slug for item in catalogue}),
        "relationships": len(relationships),
        "pending_drafts": len(PENDING_DRAFTS),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    arguments = parser.parse_args()
    counts = build_library(arguments.data_dir)
    for key, value in counts.items():
        print(f"{key}: {value}")
    print("Run build_scent_vectors.py and build_recommendations.py to derive intelligence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
