#!/usr/bin/env python3
"""Export a status/count-only, fictional public readiness report."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.platform_completion import PlatformCompletionRequest  # noqa: E402
from aromatwin.services.platform_completion import PlatformCompletionService  # noqa: E402


def main() -> int:
    result, _ = PlatformCompletionService().run(PlatformCompletionRequest(demo_mode=True))
    target = Path("data/samples/final_platform_readiness_report_sample.csv")
    with target.open("w", newline="", encoding="utf-8") as handle:
        fields = ["task_id", "status", "blocker_type", "next_action", "public_safe_summary"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for blocker in result.blockers:
            writer.writerow({"task_id": blocker.task_id, "status": "blocked",
                             "blocker_type": blocker.blocker_type,
                             "next_action": blocker.next_action,
                             "public_safe_summary": blocker.summary})
    print(f"Wrote public-safe report to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
