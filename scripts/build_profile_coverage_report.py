#!/usr/bin/env python3
"""Build private operational coverage without publishing supplier data."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from aromatwin.services.bulk_profile_generation import load_records
from aromatwin.services.profile_coverage import build_profile_coverage, coverage_summary

DEFAULT_OUTPUT = Path("data/private/reports/profile_coverage.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offers", type=Path, required=True)
    parser.add_argument("--drafts", type=Path)
    parser.add_argument("--enrichment", type=Path)
    parser.add_argument("--catalogue", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if Path("data/private").resolve() not in args.output.resolve().parents:
        parser.error("operational coverage output must be under data/private/")
    rows = build_profile_coverage(
        load_records(args.offers),
        profile_drafts=load_records(args.drafts) if args.drafts else [],
        enrichment_reviews=load_records(args.enrichment) if args.enrichment else [],
        catalogue_records=load_records(args.catalogue) if args.catalogue else [],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({**coverage_summary(rows), "records": [asdict(x) for x in rows]},
                                      indent=2) + "\n")
    counts = coverage_summary(rows)["status_counts"]
    print(f"no_profile_started={counts['no_profile_started']}")
    print(f"drafts_without_enrichment={counts['needs_enrichment'] + counts['draft_created']}")
    print(f"ready_for_admin_review={counts['enrichment_ready']}")
    print(f"ready_for_catalogue_promotion={counts['approved_for_catalogue']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
