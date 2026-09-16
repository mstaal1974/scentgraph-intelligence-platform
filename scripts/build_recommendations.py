"""Build deterministic recommendations from public catalogue and safe vector CSVs."""

import argparse
import csv
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.services.catalogue_promotion import _present_supplier_private_fields
from aromatwin.services.recommendation_engine import (
    PUBLIC_RECOMMENDATION_FIELDS,
    generate_recommendations,
)
from aromatwin.services.scent_vector_engine import VECTOR_DIMENSIONS, ScentVector

OUTPUT_FIELDS = PUBLIC_RECOMMENDATION_FIELDS


def _vector(row: dict[str, str]) -> ScentVector:
    return ScentVector(
        id=int(row["id"]),
        fragrance_id=int(row["fragrance_id"]),
        values={name: float(row.get(name) or 0) for name in VECTOR_DIMENSIONS},
        confidence_score=float(row["confidence_score"]),
        generation_method=row["generation_method"],
        review_status=row["review_status"],
        provenance_references=tuple(
            int(item) for item in row.get("provenance_references", "").split("|") if item
        ),
        source_fingerprint=row.get("source_fingerprint", ""),
        rejection_reason=row.get("rejection_reason") or None,
        restricted_content_detected=row.get("restricted_content_detected", "").lower()
        in {"1", "true", "yes"},
        private_fields_detected=bool(_present_supplier_private_fields(row)),
    )


def build_recommendations(catalogue_path: Path, vector_path: Path, output: Path) -> tuple[int, int]:
    with catalogue_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        catalogue_has_private_headers = bool(
            _present_supplier_private_fields({key: key for key in reader.fieldnames or ()})
        )
        catalogue = [
            {**row, "approved": True, "record_type": "catalogue_fragrance"} for row in reader
        ]
    with vector_path.open(newline="", encoding="utf-8-sig") as stream:
        vector_reader = csv.DictReader(stream)
        vector_has_private_headers = bool(
            _present_supplier_private_fields({key: key for key in vector_reader.fieldnames or ()})
        )
        vector_rows = list(vector_reader)
    accepted = 0
    rejected = len(catalogue) if catalogue_has_private_headers else 0
    vectors: list[ScentVector] = []
    if not vector_has_private_headers:
        for row in vector_rows:
            try:
                vectors.append(_vector(row))
            except (KeyError, TypeError, ValueError):
                rejected += 1
    else:
        rejected += len(vector_rows)

    recommendations = []
    if not catalogue_has_private_headers:
        for source in catalogue:
            try:
                generated = generate_recommendations(source, catalogue, vectors, recommendations)
            except (KeyError, TypeError, ValueError):
                rejected += 1
                continue
            for item in generated:
                if item not in recommendations:
                    recommendations.append(item)
                    accepted += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for item in recommendations:
            row = asdict(item)
            writer.writerow(
                {
                    field: json.dumps(row[field], sort_keys=True)
                    if field == "shared_dimensions_json"
                    else row[field].isoformat()
                    if isinstance(row[field], datetime)
                    else row[field]
                    if row[field] is not None
                    else ""
                    for field in OUTPUT_FIELDS
                }
            )
    return accepted, rejected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=Path("data/catalogue_fragrances.csv"))
    parser.add_argument("--vectors", type=Path, default=Path("data/scent_vectors.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/recommendations.csv"))
    args = parser.parse_args()
    accepted, rejected = build_recommendations(args.catalogue, args.vectors, args.output)
    print(f"Recommendation generation complete: accepted={accepted} rejected={rejected}")


if __name__ == "__main__":
    main()
