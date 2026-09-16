#!/usr/bin/env python3
"""Build private seller matches from private JSON inputs."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from aromatwin.schemas.seller_demand import SellerDemandBriefCreate
from aromatwin.services.seller_demand_briefs import create_brief
from aromatwin.services.seller_supplier_matching import match_brief_to_candidates

PRIVATE = Path("data/private").resolve()


def private_path(value: str) -> Path:
    path = Path(value).resolve()
    if PRIVATE not in path.parents:
        raise argparse.ArgumentTypeError("operational inputs and outputs must be under data/private/")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--briefs", type=private_path, required=True)
    parser.add_argument("--offers", type=private_path, required=True)
    parser.add_argument("--output", type=private_path,
                        default=PRIVATE / "reports/seller-demand-matches.json")
    args = parser.parse_args()
    briefs = [create_brief(SellerDemandBriefCreate(**row)) for row in json.loads(args.briefs.read_text())]
    offers = json.loads(args.offers.read_text())
    matches = [match for brief in briefs for match in match_brief_to_candidates(brief, offers)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([asdict(item) for item in matches], default=str, indent=2))
    accepted = sum(item.overall_match_score >= 0.5 for item in matches)
    print(f"accepted={accepted} rejected={len(matches) - accepted}")


if __name__ == "__main__":
    main()
