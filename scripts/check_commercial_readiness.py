#!/usr/bin/env python3
"""Check repository evidence and write the detail only to ignored private storage."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aromatwin.services.commercial_readiness import check_commercial_readiness  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("data/private/reports/commercial/readiness.json"))
    args = parser.parse_args()
    report = check_commercial_readiness()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n")
    print(f"Commercial packaging readiness: {report.overall_status}")
    for issue in report.blocking_issues:
        print(f"BLOCKER: {issue}")
    print(f"Detailed public-safe report written under private reports: {args.output}")
    return int(report.overall_status.startswith("blocked_"))


if __name__ == "__main__":
    raise SystemExit(main())
