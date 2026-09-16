#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aromatwin.services.profile_pipeline_gap_report import build_profile_pipeline_gap_report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rehearsal-id", default="fictional-rehearsal-001")
    p.add_argument(
        "--output", type=Path, default=Path("data/samples/profile_pipeline_gap_report_sample.csv")
    )
    a = p.parse_args()
    report = build_profile_pipeline_gap_report(a.rehearsal_id)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(report.gaps[0].model_fields)
    f = a.output.open("w", newline="")
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows([g.model_dump() for g in report.gaps])
    f.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
