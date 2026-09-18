#!/usr/bin/env python3
"""Generate reviewable match candidates from one prepared supplier file."""

import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from aromatwin.services.matching import candidate_from_supplier
from aromatwin.services.supplier_importer import prepare_supplier_file


def candidate_id(supplier_name: str, source_reference: str, ordinal: int) -> str:
    """Return a stable identifier for one candidate.

    The batch planner keys every candidate by id and drops any record without one, so a
    candidate that carries no identity can never reach profile generation. The source
    reference is file:row, unique per supplier row, which keeps the id stable across reruns.
    """
    seed = f"{supplier_name}|{source_reference or ordinal}"
    return f"mc-{sha256(seed.encode()).hexdigest()[:12]}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--supplier-name", required=True)
    parser.add_argument("--output", type=Path, default=Path("match-candidates.json"))
    args = parser.parse_args()
    result = prepare_supplier_file(args.input, args.supplier_name)
    candidates = []
    for ordinal, row in enumerate(result.rows, 1):
        candidate = asdict(candidate_from_supplier(row))
        candidate["match_candidate_id"] = candidate_id(
            args.supplier_name, str(candidate.get("candidate_source_reference") or ""), ordinal
        )
        candidates.append(candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidates, indent=2) + "\n")
    print(f"Wrote {len(candidates)} match candidates to {args.output}")
