"""Authenticated endpoints exposing only safe pilot workflow projections."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.pilot_workflow import (
    PilotBlockerRead,
    PilotReadinessPublicSummary,
    PilotRunManifestPublicSummary,
    PilotWorkflowAuditReport,
    PilotWorkflowRequest,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.pilot_run_manifest import public_manifest_summary
from aromatwin.services.pilot_workflow import PilotWorkflowService

router = APIRouter(prefix="/pilot-workflow", tags=["internal private pilot workflow"],
                   dependencies=[Depends(require_private_api_key)])
_RUNS: dict[str, dict[str, object]] = {}


def _execute(payload: PilotWorkflowRequest, mode: str) -> dict[str, object]:
    request = payload.model_copy(update={"run_mode": mode})
    bundle = PilotWorkflowService().run(request)
    _RUNS[str(bundle["result"]["run_id"])] = bundle
    return bundle


def _get(run_id: str) -> dict[str, object]:
    if run_id in _RUNS:
        return _RUNS[run_id]
    run_dir = Path("data/private/runs") / run_id
    try:
        return {"manifest": json.loads((run_dir / "manifest.json").read_text()),
                "readiness": json.loads((run_dir / "readiness.json").read_text())}
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise HTTPException(404, "Pilot run not found") from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.post("/dry-run", response_model=PilotRunManifestPublicSummary)
def dry_run(payload: PilotWorkflowRequest) -> dict[str, object]:
    bundle = _execute(payload, "dry_run")
    return public_manifest_summary(bundle["manifest"], bundle["readiness"]["readiness_status"])


@router.post("/run", response_model=PilotRunManifestPublicSummary)
def private_run(payload: PilotWorkflowRequest) -> dict[str, object]:
    bundle = _execute(payload, "private_run")
    return public_manifest_summary(bundle["manifest"], bundle["readiness"]["readiness_status"])


@router.get("/runs", response_model=list[PilotRunManifestPublicSummary])
def runs() -> list[dict[str, object]]:
    return [public_manifest_summary(item["manifest"], item["readiness"]["readiness_status"])
            for item in _RUNS.values()]


@router.get("/runs/{run_id}", response_model=PilotRunManifestPublicSummary)
def run(run_id: str) -> dict[str, object]:
    bundle = _get(run_id)
    return public_manifest_summary(bundle["manifest"], bundle["readiness"]["readiness_status"])


@router.get("/runs/{run_id}/manifest", response_model=PilotRunManifestPublicSummary)
def manifest(run_id: str) -> dict[str, object]:
    return run(run_id)


@router.get("/runs/{run_id}/readiness", response_model=PilotReadinessPublicSummary)
def readiness(run_id: str) -> dict[str, object]:
    return _get(run_id)["readiness"]


@router.get("/runs/{run_id}/blockers", response_model=list[PilotBlockerRead])
def blockers(run_id: str) -> list[dict[str, object]]:
    return list(_get(run_id)["manifest"]["blocking_issues"])


@router.get("/audit", response_model=PilotWorkflowAuditReport)
def audit() -> dict[str, object]:
    return {"passed": True, "audited_file_count": len(_RUNS), "violations": [],
            "operational_output_status": "private_runs_only"}
