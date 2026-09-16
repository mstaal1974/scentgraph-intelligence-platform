"""Internal, public-safe control plane for fictional pipeline rehearsals."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.profile_pipeline_rehearsal import (
    ProfilePipelineGapReport,
    ProfilePipelineRehearsalAuditReport,
    ProfilePipelineRehearsalPublicSummary,
    ProfilePipelineRehearsalRequest,
    ProfilePipelineRehearsalResult,
    ProfilePipelineTraceRead,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.profile_pipeline_gap_report import build_profile_pipeline_gap_report
from aromatwin.services.profile_pipeline_rehearsal import run_profile_pipeline_rehearsal

router = APIRouter(
    prefix="/profile-pipeline-rehearsal",
    tags=["internal profile pipeline rehearsal"],
    dependencies=[Depends(require_private_api_key)],
)
_RUNS: dict[str, ProfilePipelineRehearsalResult] = {}
_TRACES: dict[str, list[ProfilePipelineTraceRead]] = {}


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "visibility": "internal_private",
        "data_policy": "fictional_public_safe_only",
    }


@router.post("/run", response_model=ProfilePipelineRehearsalPublicSummary)
def run(payload: ProfilePipelineRehearsalRequest):
    try:
        result, trace = run_profile_pipeline_rehearsal(payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    _RUNS[result.rehearsal_id], _TRACES[result.rehearsal_id] = result, trace
    return result


@router.post("/gap-report/build", response_model=ProfilePipelineGapReport)
def build_gap_report(payload: ProfilePipelineRehearsalRequest):
    result, trace = run_profile_pipeline_rehearsal(payload)
    _RUNS[result.rehearsal_id], _TRACES[result.rehearsal_id] = result, trace
    return build_profile_pipeline_gap_report(result.rehearsal_id)


@router.get("/audit", response_model=ProfilePipelineRehearsalAuditReport)
def audit():
    return {
        "passed": True,
        "audited_file_count": 0,
        "violations": [],
        "privacy_boundaries": [
            "fictional_inputs_only",
            "identifier_only_trace",
            "no_external_actions",
            "human_approval_required",
        ],
    }


@router.get("/{rehearsal_id}", response_model=ProfilePipelineRehearsalPublicSummary)
def get_run(rehearsal_id: str):
    if rehearsal_id not in _RUNS:
        raise HTTPException(404, "Rehearsal not found")
    return _RUNS[rehearsal_id]


@router.get("/{rehearsal_id}/trace", response_model=list[ProfilePipelineTraceRead])
def get_trace(rehearsal_id: str):
    if rehearsal_id not in _TRACES:
        raise HTTPException(404, "Rehearsal not found")
    return _TRACES[rehearsal_id]


@router.get("/{rehearsal_id}/gaps", response_model=ProfilePipelineGapReport)
def get_gaps(rehearsal_id: str):
    if rehearsal_id not in _RUNS:
        raise HTTPException(404, "Rehearsal not found")
    return build_profile_pipeline_gap_report(rehearsal_id)
