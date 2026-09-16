"""Export the deterministic, public-safe Maison catalogue and recommendations."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.services.maison_integration import MaisonIntegrationService, json_cell

CATALOGUE_FIELDS = (
    "id",
    "slug",
    "title",
    "brand",
    "family",
    "notes",
    "accords",
    "mood",
    "occasion",
    "season",
    "concentration",
    "scent_vector",
    "confidence_score",
    "review_status",
    "provenance_status",
)
RECOMMENDATION_FIELDS = (
    "source_fragrance_id",
    "recommended_fragrance_id",
    "recommendation_type",
    "score",
    "confidence_score",
    "reason",
    "review_status",
    "relationship",
)


def export(data_dir: Path, catalogue_output: Path, recommendation_output: Path) -> tuple[int, int]:
    raw_count = sum(
        1 for _ in csv.DictReader((data_dir / "catalogue_fragrances.csv").open(encoding="utf-8"))
    )
    service = MaisonIntegrationService(data_dir=data_dir)
    catalogue = service.catalogue_export()
    catalogue_output.parent.mkdir(parents=True, exist_ok=True)
    with catalogue_output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CATALOGUE_FIELDS)
        writer.writeheader()
        for item in catalogue:
            row = item.model_dump()
            for field in ("notes", "accords", "mood", "occasion", "season", "scent_vector"):
                row[field] = json_cell(row[field])
            writer.writerow({field: row[field] for field in CATALOGUE_FIELDS})
    with recommendation_output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=RECOMMENDATION_FIELDS)
        writer.writeheader()
        for source in service.list_fragrances():
            for item in service.recommendations_for(source.id) or []:
                writer.writerow(
                    {
                        "source_fragrance_id": source.id,
                        "recommended_fragrance_id": item.fragrance.id,
                        **{field: getattr(item, field) for field in RECOMMENDATION_FIELDS[2:]},
                    }
                )
    return len(catalogue), raw_count - len(catalogue)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--catalogue-output", type=Path, default=Path("data/maison_catalogue_export.csv")
    )
    parser.add_argument(
        "--recommendation-output", type=Path, default=Path("data/maison_recommendation_export.csv")
    )
    args = parser.parse_args()
    accepted, rejected = export(args.data_dir, args.catalogue_output, args.recommendation_output)
    print(f"Maison export complete: accepted={accepted} rejected={rejected}")


if __name__ == "__main__":
    main()
