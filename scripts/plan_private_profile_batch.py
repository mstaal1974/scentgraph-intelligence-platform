#!/usr/bin/env python3
"""Create a bounded plan from private intake and match artifacts."""

import argparse
from pathlib import Path

from aromatwin.schemas.profile_production import ProfileBatchControls
from aromatwin.services.bulk_profile_generation import load_records
from aromatwin.services.private_supplier_intake import PrivateSupplierIntakeService
from aromatwin.services.profile_batch_planner import build_profile_batch_plan


def load_matches(root: Path) -> list[dict[str, object]]:
    records = []
    for directory in (root / "matches", root / "staging/match_candidates"):
        if directory.exists():
            for path in sorted(directory.glob("*")):
                if path.suffix.lower() in {".json", ".csv"}:
                    records.extend(load_records(path))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-profiles", type=int, default=100)
    parser.add_argument("--supplier-label")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    private = Path("data/private")
    plan = build_profile_batch_plan(
        PrivateSupplierIntakeService().scan(), load_matches(private),
        ProfileBatchControls(max_profiles=args.max_profiles, supplier_public_label=args.supplier_label, dry_run=args.dry_run),
        source_run_id=args.run_id,
    )
    if args.dry_run:
        print(plan.model_dump_json(indent=2))
    else:
        target = private / "reports" / f"{plan.batch_plan_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(target)
    return int(bool(plan.blocking_issues))


if __name__ == "__main__":
    raise SystemExit(main())
