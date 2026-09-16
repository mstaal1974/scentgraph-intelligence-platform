"""Build deterministic scent vectors from the approved public catalogue CSV."""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.services.catalogue_promotion import _present_supplier_private_fields
from aromatwin.services.scent_vector_engine import VECTOR_DIMENSIONS, generate_scent_vector

OUTPUT_FIELDS = (
    "id", "fragrance_id", *VECTOR_DIMENSIONS, "confidence_score", "generation_method",
    "review_status", "provenance_references", "source_fingerprint", "rejection_reason",
)


def build_vectors(source: Path, output: Path) -> tuple[int, int]:
    accepted = rejected = 0
    vectors = []
    with source.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        # The catalogue file is the approved projection; never accept an input private column,
        # even if a particular row leaves it blank.
        if _present_supplier_private_fields({key: key for key in row}):
            rejected += 1
            continue
        try:
            vector = generate_scent_vector({**row, "approved": True}, vectors)
        except (TypeError, ValueError):
            rejected += 1
            continue
        if not any(item.fragrance_id == vector.fragrance_id for item in vectors):
            vectors.append(vector)
            accepted += 1
        else:
            rejected += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for vector in vectors:
            row = {
                "id": vector.id,
                "fragrance_id": vector.fragrance_id,
                **vector.values,
                "confidence_score": vector.confidence_score,
                "generation_method": vector.generation_method,
                "review_status": vector.review_status,
                "provenance_references": "|".join(map(str, vector.provenance_references)),
                "source_fingerprint": vector.source_fingerprint,
                "rejection_reason": vector.rejection_reason or "",
            }
            writer.writerow(row)
    return accepted, rejected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/catalogue_fragrances.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/scent_vectors.csv"))
    args = parser.parse_args()
    accepted, rejected = build_vectors(args.source, args.output)
    print(f"Scent vector generation complete: accepted={accepted} rejected={rejected}")


if __name__ == "__main__":
    main()
