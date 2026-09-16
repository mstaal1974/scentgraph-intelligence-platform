#!/usr/bin/env python3
"""Run a safe private profile draft batch; never approve or publish."""

import argparse
from pathlib import Path

from plan_private_profile_batch import load_matches

from aromatwin.schemas.profile_production import ProfileBatchControls
from aromatwin.services.private_profile_production import run_private_profile_production
from aromatwin.services.private_supplier_intake import PrivateSupplierIntakeService
from aromatwin.services.profile_batch_planner import build_profile_batch_plan
from aromatwin.services.profile_production_readiness import assess_profile_production_readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--private-batch-run", action="store_true")
    modes.add_argument("--review-packet-only", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--max-profiles", type=int, default=100)
    parser.add_argument("--supplier-label")
    args = parser.parse_args()
    mode = "private_batch_run" if args.private_batch_run else "review_packet_only" if args.review_packet_only else "dry_run"
    intakes = PrivateSupplierIntakeService().scan()
    matches = load_matches(Path("data/private"))
    readiness = assess_profile_production_readiness(intake_manifests=intakes, match_candidate_count=len(matches))
    if readiness.overall_status != "ready_for_private_profile_batch":
        print(readiness.model_dump_json(indent=2))
        return 2
    controls = ProfileBatchControls(max_profiles=args.max_profiles, supplier_public_label=args.supplier_label, dry_run=mode == "dry_run")
    plan = build_profile_batch_plan(intakes, matches, controls, source_run_id=args.run_id)
    if plan.blocking_issues:
        print(plan.model_dump_json(indent=2))
        return 2
    run, _, _ = run_private_profile_production(plan, matches, mode=mode, run_id=args.run_id)
    print(run.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
