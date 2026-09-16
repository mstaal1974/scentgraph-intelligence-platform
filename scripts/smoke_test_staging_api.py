#!/usr/bin/env python3
"""Run public-safe checks against an operator-selected staging API."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.staging_smoke import StagingSmokeRunRequest  # noqa: E402
from aromatwin.services.staging_smoke_tests import (  # noqa: E402
    public_summary,
    run_staging_smoke_tests,
)

PRIVATE_REPORT_ROOT = Path("data/private/reports").resolve()


def _output_path(value: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else Path.cwd() / path
    resolved = path.resolve()
    if resolved != PRIVATE_REPORT_ROOT and PRIVATE_REPORT_ROOT not in resolved.parents:
        raise argparse.ArgumentTypeError("output must be under data/private/reports/")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("AROMATWIN_STAGING_BASE_URL"))
    parser.add_argument("--expected-environment", default="staging")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--include-openapi", action="store_true")
    parser.add_argument("--skip-private-checks", action="store_true")
    parser.add_argument("--output", type=_output_path)
    args = parser.parse_args(argv)
    if not args.base_url:
        parser.error("--base-url or AROMATWIN_STAGING_BASE_URL is required")
    request = StagingSmokeRunRequest(
        base_url=args.base_url,
        private_api_key=os.getenv("AROMATWIN_STAGING_PRIVATE_API_KEY"),
        timeout_seconds=args.timeout,
        expected_environment=args.expected_environment,
        include_openapi_check=args.include_openapi,
        include_private_checks=not args.skip_private_checks,
    )
    result = run_staging_smoke_tests(request)
    print(json.dumps(public_summary(result).model_dump(mode="json"), indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
        print("Private, sanitized smoke detail written under data/private/reports/.")
    return int(result.overall_status.startswith("blocked_"))


if __name__ == "__main__":
    raise SystemExit(main())
