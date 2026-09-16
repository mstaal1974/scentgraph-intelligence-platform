#!/usr/bin/env python3
"""Prepare an offline private research queue; performs no searching or scraping."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from aromatwin.services.bulk_profile_generation import load_records
from aromatwin.services.enrichment_research_queue import build_enrichment_research_queue

DEFAULT_OUTPUT = Path("data/private/reports/enrichment_research_queue.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--drafts", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if Path("data/private").resolve() not in args.output.resolve().parents:
        parser.error("operational research queue output must be under data/private/")
    coverage = load_records(args.coverage)
    drafts = load_records(args.drafts) if args.drafts else []
    queue = build_enrichment_research_queue(coverage, drafts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([asdict(item) for item in queue], indent=2) + "\n")
    print(f"research_queue_items={len(queue)}")
    print("network_searches=0 catalogue_promotions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
