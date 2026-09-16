#!/usr/bin/env python3
"""Export status-only private profile production readiness."""

import argparse
from pathlib import Path

from aromatwin.services.profile_production_readiness import assess_profile_production_readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/private/reports/profile_production_readiness.json"))
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(Path("data/private").resolve()):
        raise SystemExit("Detailed readiness reports must remain under data/private")
    report = assess_profile_production_readiness()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
