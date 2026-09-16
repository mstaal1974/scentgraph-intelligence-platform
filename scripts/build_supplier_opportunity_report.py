#!/usr/bin/env python3
"""Aggregate private match output into anonymised supplier opportunities."""

import argparse
import json
from pathlib import Path

from aromatwin.services.seller_supplier_matching import SellerSupplierMatch
from aromatwin.services.supplier_opportunity_intelligence import build_supplier_opportunities

PRIVATE = Path("data/private").resolve()


def private_path(value: str) -> Path:
    path = Path(value).resolve()
    if PRIVATE not in path.parents:
        raise argparse.ArgumentTypeError("operational inputs and outputs must be under data/private/")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches", type=private_path, required=True)
    parser.add_argument("--output", type=private_path,
                        default=PRIVATE / "reports/supplier-opportunities.json")
    args = parser.parse_args()
    matches = [SellerSupplierMatch(**row) for row in json.loads(args.matches.read_text())]
    report = build_supplier_opportunities(matches)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(f"opportunities={len(report)} anonymised=true")


if __name__ == "__main__":
    main()
