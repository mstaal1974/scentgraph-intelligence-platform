#!/usr/bin/env python3
"""Run safe completion checks and optionally persist a private detailed handoff report."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aromatwin.schemas.platform_completion import PlatformCompletionRequest  # noqa: E402
from aromatwin.services.platform_completion import PlatformCompletionService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--export-private", action="store_true")
    args = parser.parse_args()
    result, report = PlatformCompletionService().run(
        PlatformCompletionRequest(demo_mode=args.demo))
    if args.export_private:
        target = Path("data/private/reports") / f"{result.completion_run_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"result": result.model_dump(mode="json"),
                                      "readiness": report.model_dump(mode="json")}, indent=2) + "\n")
    print(f"Final status: {result.final_platform_status}")
    print(f"Completed: {result.completed_count}; blocked: {result.blocked_count}; failed: {result.failed_count}")
    for action in result.recommended_next_actions:
        print(f"NEXT: {action}")
    return int(result.failed_count > 0)


if __name__ == "__main__":
    raise SystemExit(main())
