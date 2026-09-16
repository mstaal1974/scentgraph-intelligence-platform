#!/usr/bin/env python3
"""Generate fictional/sample completion readiness; never reads private supplier inputs."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.platform_completion import PlatformCompletionRequest  # noqa: E402
from aromatwin.services.platform_completion import PlatformCompletionService  # noqa: E402


def main() -> int:
    result, report = PlatformCompletionService().run(PlatformCompletionRequest(demo_mode=True))
    target = Path("data/samples/final_platform_readiness_report_sample.csv")
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["readiness_status", "completed_count",
                                                    "blocked_count", "public_safe_summary"])
        writer.writeheader()
        writer.writerow({"readiness_status": report.final_platform_status,
                         "completed_count": result.completed_count,
                         "blocked_count": result.blocked_count,
                         "public_safe_summary": "Fictional demo; manual gates remain blocked."})
    print(f"Demo completion: {result.final_platform_status}")
    return int(result.failed_count > 0)


if __name__ == "__main__":
    raise SystemExit(main())
