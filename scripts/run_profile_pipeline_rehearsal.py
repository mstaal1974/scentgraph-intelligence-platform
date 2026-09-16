#!/usr/bin/env python3
"""Run a fictional profile-pipeline rehearsal; no external actions are possible."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aromatwin.schemas.profile_pipeline_rehearsal import ProfilePipelineRehearsalRequest
from aromatwin.services.profile_pipeline_rehearsal import run_profile_pipeline_rehearsal


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["dry_rehearsal", "sample_private_rehearsal", "trace_only"],
        default="dry_rehearsal",
    )
    parser.add_argument("--max-candidates", type=int, default=1)
    parser.add_argument("--write-private", action="store_true")
    args = parser.parse_args()
    result, trace = run_profile_pipeline_rehearsal(
        ProfilePipelineRehearsalRequest(
            rehearsal_mode=args.mode, max_candidates=args.max_candidates
        )
    )
    if args.write_private:
        target = Path("data/private/reports/rehearsals") / f"{result.rehearsal_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "result": result.model_dump(mode="json"),
                    "trace": [r.model_dump(mode="json") for r in trace],
                },
                indent=2,
            )
        )
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
