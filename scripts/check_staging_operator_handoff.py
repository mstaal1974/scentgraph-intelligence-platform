#!/usr/bin/env python3
"""Evaluate manual staging handoff confirmations without requesting secret values."""

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.staging_smoke import StagingOperatorHandoffChecklist  # noqa: E402

STEPS = (
    "staging_host_selected", "staging_url_available", "private_api_key_configured_in_host",
    "database_configured", "migrations_considered", "private_storage_configured",
    "cors_configured", "deployment_readiness_check_run", "smoke_test_run",
    "private_supplier_upload_location_confirmed", "human_review_process_confirmed",
    "rollback_process_documented",
)
VALID = {"complete", "ready", "missing", "blocked", "manual_required"}


def build_checklist(values: dict[str, str]) -> StagingOperatorHandoffChecklist:
    steps = {name: values.get(name, "manual_required") for name in STEPS}
    invalid = {value for value in steps.values() if value not in VALID}
    if invalid:
        raise ValueError(f"Unsupported checklist status: {sorted(invalid)}")
    overall = "blocked" if "blocked" in steps.values() else ("missing" if "missing" in steps.values() else ("manual_required" if "manual_required" in steps.values() else ("ready" if "ready" in steps.values() else "complete")))
    pending = next((name for name, status in steps.items() if status not in {"complete", "ready"}), None)
    return StagingOperatorHandoffChecklist(
        checklist_id=f"handoff-{uuid4()}", overall_status=overall, steps=steps,
        completed_count=sum(value == "complete" for value in steps.values()),
        manual_required_count=sum(value == "manual_required" for value in steps.values()),
        missing_count=sum(value == "missing" for value in steps.values()),
        blocked_count=sum(value == "blocked" for value in steps.values()),
        recommended_next_action=f"Confirm manual step: {pending}." if pending else "Operator handoff is complete.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checklist", type=Path, help="JSON mapping of step names to statuses")
    args = parser.parse_args(argv)
    values = json.loads(args.checklist.read_text(encoding="utf-8")) if args.checklist else {}
    checklist = build_checklist(values)
    print(json.dumps(checklist.model_dump(mode="json"), indent=2))
    return int(checklist.overall_status in {"missing", "blocked"})


if __name__ == "__main__":
    raise SystemExit(main())
