#!/usr/bin/env python3
"""Create a local readiness report without loading or printing private record values."""
import argparse
import json
from pathlib import Path

from aromatwin.services.maison_integration_readiness import check_maison_integration_readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/maison/readiness.json"))
    args = parser.parse_args()
    report = check_maison_integration_readiness()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n")
    print(f"Maison readiness: {report.overall_status}")
    for issue in report.blocking_issues:
        print(f"BLOCKER: {issue}")
    print(f"Detailed public-safe report written under private reports: {args.output}")
    return int(report.overall_status.startswith("blocked_privacy"))


if __name__ == "__main__":
    raise SystemExit(main())
