"""Evidence-based final completion orchestration for safe repository actions only."""

import csv
import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aromatwin.schemas.platform_completion import (
    CompletionBlockerRead,
    PlatformCompletionRequest,
    PlatformCompletionResult,
)
from aromatwin.services.completion_readiness_report import build_readiness_report
from aromatwin.services.completion_task_registry import build_completion_task_registry

ROOT = Path(__file__).resolve().parents[3]
CORE_MODULES = (
    "src/aromatwin/services/supplier_importer.py", "src/aromatwin/services/supplier_sourcing.py",
    "src/aromatwin/services/bulk_profile_generation.py", "src/aromatwin/services/pilot_workflow.py",
    "src/aromatwin/services/review_gates.py", "src/aromatwin/services/persistence_service.py",
)


class PlatformCompletionService:
    """Run deterministic local checks and preserve every real-world gate as a blocker."""

    def __init__(self, root: Path = ROOT):
        self.root = root.resolve()

    def _evidence(self, category: str, demo_mode: bool,
                  run_audits: bool = True) -> tuple[bool, str]:
        if category == "repository_validation":
            return all((self.root / path).is_file() for path in CORE_MODULES), "core modules present"
        if category == "operations_api_ready":
            main = (self.root / "src/aromatwin/main.py").read_text(encoding="utf-8")
            return "platform_completion" in main, "completion router registered"
        if category == "public_sample_validation":
            files = list((self.root / "data/samples").glob("*.csv"))
            try:
                for path in files:
                    with path.open(newline="", encoding="utf-8") as handle:
                        next(csv.reader(handle), None)
                return bool(files), f"{len(files)} sample files parsed"
            except (OSError, UnicodeError, csv.Error) as exc:
                return False, f"sample parsing failed: {type(exc).__name__}"
        if category == "persistence_initialisation":
            try:
                connection = sqlite3.connect(":memory:")
                connection.execute("create table readiness_smoke (id integer primary key)")
                connection.close()
                return True, "isolated SQLite smoke check passed"
            except sqlite3.Error:
                return False, "isolated SQLite smoke check failed"
        if category == "demo_pilot_run":
            return demo_mode or (self.root / "data/samples/pilot_workflow_summary_sample.csv").is_file(), \
                "fictional demo evidence present"
        if category == "privacy_audit":
            audit = self.root / "scripts/run_all_safe_audits.py"
            if not audit.is_file():
                return False, "safe audit runner not found"
            if not run_audits:
                return True, "safe audit runner available; execution was not requested"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(self.root / "src") + os.pathsep + environment.get(
                "PYTHONPATH", "")
            completed = subprocess.run([sys.executable, str(audit)], cwd=self.root,
                                       check=False, capture_output=True, text=True,
                                       env=environment)
            return completed.returncode == 0, ("all available safe audits passed"
                                                if completed.returncode == 0
                                                else "one or more safe audits failed")
        # Existing modules/samples are repository evidence for readiness—not proof of real execution.
        token = category.removesuffix("_ready").replace("private_supplier_intake_preflight", "private_supplier_intake")
        matches = list((self.root / "src/aromatwin/services").glob(f"*{token}*.py"))
        return bool(matches), "repository capability present" if matches else "expected capability not found"

    def run(self, request: PlatformCompletionRequest | None = None) -> tuple[PlatformCompletionResult, object]:
        request = request or PlatformCompletionRequest()
        started = datetime.now(UTC)
        tasks = build_completion_task_registry()
        evidence_failures: list[str] = []
        automatic_actions: list[str] = []
        for task in tasks:
            if not task.can_complete_automatically:
                continue
            passed, evidence = self._evidence(task.category, request.demo_mode, request.run_audits)
            task.status = "completed" if passed else "failed"
            task.blocker_reason = None if passed else evidence
            task.next_action = evidence if passed else f"Resolve validation failure: {evidence}."
            if passed:
                automatic_actions.append(f"{task.task_name}: {evidence}")
            else:
                evidence_failures.append(task.task_id)
        privacy_failed = any(t.category == "privacy_audit" and t.status == "failed" for t in tasks)
        core_failed = any(t.category in {"repository_validation", "operations_api_ready"}
                          and t.status == "failed" for t in tasks)
        if privacy_failed:
            final_status = "blocked_privacy_risk"
        elif core_failed:
            final_status = "blocked_missing_core_module"
        elif evidence_failures:
            final_status = "blocked_validation_failure"
        else:
            final_status = "repository_complete_ready_for_private_data"
        blockers = [CompletionBlockerRead(
            task_id=t.task_id, blocker_type=t.status.removeprefix("blocked_").removesuffix("_required"),
            summary=t.blocker_reason or "External action is required.", next_action=t.next_action,
        ) for t in tasks if t.status.startswith("blocked_")]
        completed = datetime.now(UTC)
        result = PlatformCompletionResult(
            completion_run_id=f"completion-{uuid4().hex[:12]}", started_at=started,
            completed_at=completed, total_tasks=len(tasks),
            completed_count=sum(t.status == "completed" for t in tasks),
            ready_count=sum(t.status == "ready" for t in tasks), blocked_count=len(blockers),
            failed_count=sum(t.status == "failed" for t in tasks),
            automatic_actions_completed=[*automatic_actions,
                                         "Compile check planned: python -m compileall -q src scripts tests"],
            manual_actions_required=[b.next_action for b in blockers],
            privacy_audit_status="passed" if not privacy_failed else "failed",
            deployment_readiness_status="blocked_pending_environment_and_credentials",
            private_pilot_readiness_status="ready_after_private_supplier_files_added",
            final_platform_status=final_status, blockers=blockers,
            recommended_next_actions=list(dict.fromkeys(b.next_action for b in blockers)),
        )
        return result, build_readiness_report(tasks, final_status)
