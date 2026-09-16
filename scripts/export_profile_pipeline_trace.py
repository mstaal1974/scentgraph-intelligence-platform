#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aromatwin.services.profile_pipeline_trace import build_profile_pipeline_trace


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rehearsal-id", default="fictional-rehearsal-001")
    p.add_argument(
        "--output",
        type=Path,
        default=Path("data/samples/profile_pipeline_rehearsal_trace_sample.csv"),
    )
    a = p.parse_args()
    rows = build_profile_pipeline_trace(a.rehearsal_id)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "trace_id",
        "rehearsal_id",
        "candidate_id",
        "stage_name",
        "input_reference",
        "output_reference",
        "status",
        "public_safe_summary",
        "privacy_status",
        "next_stage",
        "blocking_issue",
        "created_at",
    ]
    with a.output.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows([r.model_dump(mode="json") for r in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
