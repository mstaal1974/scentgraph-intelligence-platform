#!/usr/bin/env python3
"""Enrich a bounded private profile batch without creating public artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aromatwin.services.profile_enrichment import (  # noqa: E402
    DEFAULT_MODEL,
    MODEL_PROVENANCE,
    OfflineHeuristicEnrichmentProvider,
    OpenAIEnrichmentProvider,
)

PRIVATE_ROOT = (REPOSITORY_ROOT / "data/private").resolve()


def enrich_batch(
    run_id: str,
    max_profiles: int,
    provider_name: str = "offline",
    *,
    private_root: Path = PRIVATE_ROOT,
    model: str = DEFAULT_MODEL,
) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", run_id):
        raise ValueError("Invalid run ID")
    if max_profiles < 1:
        raise ValueError("max_profiles must be positive")
    root = private_root.resolve()
    profiles = (root / "runs" / run_id / "profiles").resolve()
    if not profiles.is_relative_to(root):
        raise ValueError("Output must remain under data/private")
    drafts_path = profiles / "drafts.json"
    drafts = json.loads(drafts_path.read_text(encoding="utf-8"))
    if not isinstance(drafts, list):
        raise ValueError("drafts.json must contain a list")
    provider = (
        OfflineHeuristicEnrichmentProvider()
        if provider_name == "offline"
        else OpenAIEnrichmentProvider(model=model)
    )
    if not provider.is_available:
        raise RuntimeError("OpenAI enrichment skipped: OPENAI_API_KEY is not configured")
    enriched = [provider.enrich(row) for row in drafts[:max_profiles]]
    asserted = sum(
        1
        for row in enriched
        for value in row.get("field_provenance", {}).values()
        if value == MODEL_PROVENANCE
    )
    print(
        f"Enriched {len(enriched)} profiles with {asserted} model-asserted fields awaiting "
        "human review."
    )
    destination = profiles / "enriched_profiles.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(enriched, indent=2) + "\n", encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-profiles", type=int, default=25)
    parser.add_argument("--provider", choices=("offline", "openai"), default="offline")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id for --provider openai.")
    args = parser.parse_args()
    try:
        print(enrich_batch(args.run_id, args.max_profiles, args.provider, model=args.model))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
