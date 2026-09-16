#!/usr/bin/env python3
"""Build a public-safe staging deployment report; never deploy resources."""

import argparse
import json
from pathlib import Path

from aromatwin.services.deployment_readiness import check_deployment_readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = check_deployment_readiness()
    payload = report.model_dump(mode="json")
    print(json.dumps(payload, indent=2))
    if args.write_report:
        target = Path("data/private/reports/deployment_readiness.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote masked report to {target}")
    return int(report.overall_status.startswith("blocked_"))


if __name__ == "__main__":
    raise SystemExit(main())
