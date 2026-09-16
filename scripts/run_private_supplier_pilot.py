#!/usr/bin/env python3
"""Build a preflight plan and a non-approving private pilot acceptance report."""

import argparse
import json
from pathlib import Path

from aromatwin.schemas.private_supplier_pilot import PilotExecutionPlanRequest
from aromatwin.services.pilot_acceptance_report import build_acceptance_report
from aromatwin.services.pilot_execution_plan import build_execution_plan
from aromatwin.services.pilot_workflow import PILOT_STAGES, PilotWorkflowService
from aromatwin.services.private_supplier_intake import PrivateSupplierIntakeService


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--private-run", action="store_true")
    modes.add_argument("--review-only-run", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--supplier-label")
    parser.add_argument("--stages")
    args = parser.parse_args()
    mode = "private_run" if args.private_run else "review_only_run" if args.review_only_run else "dry_run"
    request = PilotExecutionPlanRequest(run_id=args.run_id, run_mode=mode,
        supplier_labels=[args.supplier_label] if args.supplier_label else [],
        selected_stages=args.stages.split(",") if args.stages else None)
    plan = build_execution_plan(request, PrivateSupplierIntakeService().scan())
    workflow_stages = [stage for stage in plan.stage_sequence if stage in PILOT_STAGES]
    if mode != "review_only_run" and not plan.blocking_issues and workflow_stages:
        bundle = PilotWorkflowService().run({"run_id": plan.run_id, "run_mode": mode,
            "stages": workflow_stages, "input_locations": plan.selected_supplier_files})
        results = bundle["result"]["stage_results"]
    else:
        results = [{"stage": stage,
                    "status": "preflight_ready" if not plan.blocking_issues else "blocked",
                    "blocked_count": int(bool(plan.blocking_issues)), "review_required_count": 1}
                   for stage in plan.stage_sequence]
    report = build_acceptance_report(plan.run_id, results)
    if mode == "private_run":
        destination = Path("data/private/runs") / plan.run_id
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "execution_plan.json").write_text(plan.model_dump_json(indent=2) + "\n")
        (destination / "acceptance.json").write_text(report.model_dump_json(indent=2) + "\n")
    print(json.dumps({"run_id": plan.run_id, "mode": mode, "stages": plan.stage_sequence,
        "blockers": plan.blocking_issues, "acceptance_status": report.overall_status}, indent=2))
    return int(bool(plan.blocking_issues))


if __name__ == "__main__":
    raise SystemExit(main())
