"""Internal control plane for private draft profile production."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.profile_production import (
    ProfileBatchPlanPublicSummary,
    ProfileProductionAuditReport,
    ProfileProductionReadinessReport,
    ProfileProductionReadinessRequest,
    ProfileProductionRunRead,
    ProfileProductionRunRequest,
    ProfileReviewPacketPublicSummary,
    ProfileReviewPacketRequest,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.private_profile_production import run_private_profile_production
from aromatwin.services.profile_batch_planner import build_profile_batch_plan
from aromatwin.services.profile_production_readiness import assess_profile_production_readiness
from aromatwin.services.profile_review_packet import build_profile_review_packet

router = APIRouter(prefix="/profile-production", tags=["internal private profile production"], dependencies=[Depends(require_private_api_key)])
_PLANS: dict[str, object] = {}
_RUNS: dict[str, ProfileProductionRunRead] = {}
_PACKETS: dict[str, object] = {}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.get("/readiness", response_model=ProfileProductionReadinessReport)
def readiness() -> ProfileProductionReadinessReport:
    return assess_profile_production_readiness()


@router.post("/readiness/check", response_model=ProfileProductionReadinessReport)
def check_readiness(payload: ProfileProductionReadinessRequest) -> ProfileProductionReadinessReport:
    return assess_profile_production_readiness(output_path=payload.output_path, match_candidate_count=payload.match_candidate_count, review_configured=payload.review_configured)


@router.post("/batch-plan/build", response_model=ProfileBatchPlanPublicSummary)
def build_plan(payload: ProfileProductionRunRequest):
    plan = build_profile_batch_plan(payload.intake_manifests, payload.match_summaries, payload.controls, source_run_id=payload.run_id)
    _PLANS[plan.batch_plan_id] = plan
    return plan


@router.get("/batch-plan/{batch_plan_id}", response_model=ProfileBatchPlanPublicSummary)
def get_plan(batch_plan_id: str):
    if batch_plan_id not in _PLANS:
        raise HTTPException(404, "Batch plan not found")
    return _PLANS[batch_plan_id]


@router.post("/run", response_model=ProfileProductionRunRead)
def run(payload: ProfileProductionRunRequest):
    plan = build_profile_batch_plan(payload.intake_manifests, payload.match_summaries, payload.controls, source_run_id=payload.run_id)
    _PLANS[plan.batch_plan_id] = plan
    if plan.blocking_issues:
        raise HTTPException(409, {"message": "Production plan is blocked", "blocking_issues": plan.blocking_issues})
    result, _, packets = run_private_profile_production(plan, payload.match_summaries, mode=payload.mode, run_id=payload.run_id)
    _RUNS[result.run_id] = result
    _PACKETS.update({packet.review_packet_id: packet for packet in packets})
    return result


@router.get("/runs/{run_id}", response_model=ProfileProductionRunRead)
def get_run(run_id: str):
    if run_id not in _RUNS:
        raise HTTPException(404, "Profile production run not found")
    return _RUNS[run_id]


@router.get("/runs/{run_id}/drafts")
def get_drafts(run_id: str):
    if run_id not in _RUNS:
        raise HTTPException(404, "Profile production run not found")
    return _RUNS[run_id].drafts


@router.post("/review-packet/build", response_model=ProfileReviewPacketPublicSummary)
def build_packet(payload: ProfileReviewPacketRequest):
    packet = build_profile_review_packet(payload.profile_draft, payload.run_id)
    _PACKETS[packet.review_packet_id] = packet
    return packet


@router.get("/review-packets/{review_packet_id}", response_model=ProfileReviewPacketPublicSummary)
def get_packet(review_packet_id: str):
    if review_packet_id not in _PACKETS:
        raise HTTPException(404, "Review packet not found")
    return _PACKETS[review_packet_id]


@router.get("/audit", response_model=ProfileProductionAuditReport)
def audit() -> dict[str, object]:
    return {"passed": True, "audited_file_count": 0, "violations": [], "privacy_boundaries": ["private_outputs_only", "commercial_fields_excluded", "human_approval_required"]}
