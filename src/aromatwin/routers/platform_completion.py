"""Authenticated, public-safe API for repository completion and operator handoff."""

import json
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends

from aromatwin.schemas.platform_completion import (
    CompletionAuditReport,
    CompletionBlockerRead,
    CompletionReadinessReport,
    CompletionTaskPublicSummary,
    PlatformCompletionRequest,
    PlatformCompletionResult,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.completion_task_registry import build_completion_task_registry, public_task
from aromatwin.services.platform_completion import PlatformCompletionService

router = APIRouter(prefix="/platform-completion", tags=["internal platform completion"],
                   dependencies=[Depends(require_private_api_key)])
_LATEST: tuple[PlatformCompletionResult, CompletionReadinessReport] | None = None


def _run(request: PlatformCompletionRequest | None = None):
    global _LATEST
    _LATEST = PlatformCompletionService().run(request)
    return _LATEST


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.get("/tasks", response_model=list[CompletionTaskPublicSummary])
def tasks():
    return [public_task(task) for task in build_completion_task_registry()]


@router.post("/run-safe-checks", response_model=PlatformCompletionResult)
def run_safe_checks(payload: PlatformCompletionRequest):
    payload.demo_mode = False
    return _run(payload)[0]


@router.post("/run-demo-completion", response_model=PlatformCompletionResult)
def run_demo_completion(payload: PlatformCompletionRequest):
    payload.demo_mode = True
    return _run(payload)[0]


@router.get("/readiness", response_model=CompletionReadinessReport)
def readiness():
    return (_LATEST or _run())[1]


@router.get("/blockers", response_model=list[CompletionBlockerRead])
def blockers():
    return (_LATEST or _run())[0].blockers


@router.post("/readiness/export", response_model=CompletionReadinessReport)
def export_readiness():
    report = (_LATEST or _run())[1]
    target = Path("data/private/reports/final_platform_readiness.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return report


@router.get("/audit", response_model=CompletionAuditReport)
def audit():
    files = list(Path("data/samples").glob("*platform*completion*.csv"))
    files += list(Path("data/samples").glob("final_platform_readiness*.csv"))
    completed = subprocess.run(
        [sys.executable, "scripts/audit_platform_completion_privacy.py"],
        check=False, capture_output=True, text=True,
    )
    violations = [] if completed.returncode == 0 else ["Public completion privacy audit failed."]
    return {"passed": completed.returncode == 0, "audited_file_count": len(files),
            "violations": violations}
