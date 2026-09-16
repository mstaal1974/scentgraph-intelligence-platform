#!/usr/bin/env python3
"""Run the evidence-only private pilot workflow from the command line."""

import argparse
from pathlib import Path

from aromatwin.services.pilot_workflow import PILOT_STAGES, PilotWorkflowService


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--demo-sample", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--stages", help="Comma-separated stage names")
    parser.add_argument("--input", action="append", default=[])
    args = parser.parse_args()
    run_mode = "demo_sample" if args.demo_sample else "dry_run" if args.dry_run else "private_run"
    stages = [value.strip() for value in args.stages.split(",") if value.strip()] \
        if args.stages else list(PILOT_STAGES)
    bundle = PilotWorkflowService(Path("data")).run({"run_id": args.run_id,
        "run_mode": run_mode, "stages": stages, "input_locations": args.input})
    result = bundle["result"]
    print(f"Run: {result['run_id']} ({run_mode})")
    for item in result["stage_results"]:
        print(f"- {item['stage']}: {item['status']}")
    blockers = bundle["manifest"]["blocking_issues"]
    print("Blockers:")
    for blocker in blockers:
        print(f"- [{blocker['severity']}] {blocker['summary']} -> {blocker['recommended_fix']}")
    print(f"Readiness: {result['readiness_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
