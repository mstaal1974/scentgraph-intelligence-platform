#!/usr/bin/env python3
"""Build operational launch priorities without publishing source records."""
import argparse
import json
from pathlib import Path

from aromatwin.services.launch_intelligence import build_launch_intelligence, public_summary


def load_candidates(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("candidates", payload) if isinstance(payload, dict) else payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/private/launch_candidates.json"))
    parser.add_argument("--output", type=Path, default=Path("data/private/reports/launch_priority.json"))
    parser.add_argument("--public-output", type=Path)
    args = parser.parse_args()
    records = build_launch_intelligence(load_candidates(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, default=str, indent=2), encoding="utf-8")
    if args.public_output:
        if args.public_output.parent != Path("data/samples"):
            raise SystemExit("Public demo output must be written directly under data/samples/")
        args.public_output.write_text(json.dumps([public_summary(r) for r in records], default=str, indent=2), encoding="utf-8")
    print("launch_now:", sum(r["launch_status"] == "launch_now" for r in records))
    print("hold:", sum(str(r["launch_status"]).startswith("hold_") for r in records))
    print("enrichment_needed:", sum(r["launch_status"] == "launch_after_profile_enrichment" for r in records))
    print("top:", [(r["launch_candidate_id"], r["launch_priority_band"]) for r in records[:10]])

if __name__ == "__main__":
    main()
