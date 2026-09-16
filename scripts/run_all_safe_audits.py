#!/usr/bin/env python3
"""Run every available repository validation/privacy audit without private inputs."""

import json
import os
import subprocess
import sys
from pathlib import Path

COMMANDS = [
    ["scripts/validate_data.py", "data"], ["scripts/audit_supplier_data.py"],
    ["scripts/audit_supplier_offers.py"], ["scripts/audit_seller_supplier_matching.py"],
    ["scripts/audit_consumer_scent_privacy.py"],
    ["scripts/audit_launch_intelligence_privacy.py"],
    ["scripts/audit_pilot_workflow_privacy.py"], ["scripts/audit_persistence_privacy.py"],
    ["scripts/audit_review_workflow_privacy.py"], ["scripts/audit_private_pilot_inputs.py"],
    ["scripts/audit_platform_completion_privacy.py"],
]


def run_all(root: Path = Path(".")) -> tuple[int, list[dict[str, str]]]:
    results = []
    failed = False
    environment = os.environ.copy()
    source_path = str((root / "src").resolve())
    environment["PYTHONPATH"] = source_path + os.pathsep + environment.get("PYTHONPATH", "")
    for command in COMMANDS:
        path = root / command[0]
        if not path.is_file():
            print(f"WARNING: skipping missing optional audit: {command[0]}")
            results.append({"audit": command[0], "status": "skipped_missing"})
            continue
        completed = subprocess.run([sys.executable, *command], cwd=root, check=False,
                                   capture_output=True, text=True, env=environment)
        status = "passed" if completed.returncode == 0 else "failed"
        results.append({"audit": command[0], "status": status})
        print(f"{status.upper()}: {' '.join(command)}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.returncode:
            failed = True
            if completed.stderr.strip():
                print(completed.stderr.strip(), file=sys.stderr)
    return int(failed), results


def main() -> int:
    code, results = run_all()
    target = Path("data/samples/platform_completion_audit_summary.json")
    target.write_text(json.dumps({"audits": results}, indent=2) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
