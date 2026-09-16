#!/usr/bin/env python3
"""Print a masked environment readiness report."""

import json

from aromatwin.services.environment_readiness import BLOCKING, check_environment_readiness


def main() -> int:
    report = check_environment_readiness()
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return int(report.overall_status in BLOCKING)


if __name__ == "__main__":
    raise SystemExit(main())
