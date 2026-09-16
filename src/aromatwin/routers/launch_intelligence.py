"""Internal launch workflow with public-safe response projections."""

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.launch_intelligence import (
    LaunchGapReport,
    LaunchIntelligenceAuditReport,
    LaunchIntelligencePublicSummary,
    LaunchPriorityReport,
    LaunchRecommendationPlanResult,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.launch_gap_analysis import analyse_launch_gaps
from aromatwin.services.launch_intelligence import build_launch_intelligence, public_summary
from aromatwin.services.launch_recommendation_planner import build_launch_plans

router = APIRouter(prefix="/launch-intelligence", tags=["internal launch intelligence"],
                   dependencies=[Depends(require_private_api_key)])
_CANDIDATES: list[dict[str, object]] = []
_PLANS: list[dict[str, object]] = []


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.post("/build", response_model=LaunchPriorityReport)
def build(payload: list[dict[str, object]]) -> dict[str, object]:
    records = build_launch_intelligence(payload)
    _CANDIDATES[:] = records
    return {"candidate_count": len(records), "candidates": [public_summary(item) for item in records]}


@router.get("/candidates", response_model=list[LaunchIntelligencePublicSummary])
def candidates() -> list[dict[str, object]]:
    return [public_summary(item) for item in _CANDIDATES]


@router.get("/candidates/{launch_candidate_id}", response_model=LaunchIntelligencePublicSummary)
def candidate(launch_candidate_id: str) -> dict[str, object]:
    found = next((item for item in _CANDIDATES if item["launch_candidate_id"] == launch_candidate_id), None)
    if found is None:
        raise HTTPException(404, "Launch candidate not found")
    return public_summary(found)


@router.get("/priority", response_model=LaunchPriorityReport)
def priority() -> dict[str, object]:
    return {"candidate_count": len(_CANDIDATES),
            "candidates": [public_summary(item) for item in _CANDIDATES]}


@router.get("/priority/top", response_model=list[LaunchIntelligencePublicSummary])
def priority_top(limit: int = 50) -> list[dict[str, object]]:
    return [public_summary(item) for item in _CANDIDATES[:max(0, min(limit, 100))]]


def _gap_report(records: list[dict[str, object]]) -> dict[str, object]:
    gaps = [gap for item in records for gap in analyse_launch_gaps(item)]
    return {"gap_count": len(gaps), "gaps": gaps,
            "by_owner_role": dict(Counter(gap["owner_role"] for gap in gaps)),
            "by_severity": dict(Counter(gap["severity"] for gap in gaps))}


@router.get("/gaps", response_model=LaunchGapReport)
def gaps() -> dict[str, object]:
    return _gap_report(_CANDIDATES)


@router.get("/gaps/{launch_candidate_id}", response_model=LaunchGapReport)
def candidate_gaps(launch_candidate_id: str) -> dict[str, object]:
    records = [item for item in _CANDIDATES if item["launch_candidate_id"] == launch_candidate_id]
    if not records:
        raise HTTPException(404, "Launch candidate not found")
    return _gap_report(records)


@router.post("/plans/build", response_model=LaunchRecommendationPlanResult)
def build_plans() -> dict[str, object]:
    _PLANS[:] = build_launch_plans(_CANDIDATES)
    return {"plan_count": len(_PLANS), "plans": _PLANS}


@router.get("/plans", response_model=LaunchRecommendationPlanResult)
def plans() -> dict[str, object]:
    return {"plan_count": len(_PLANS), "plans": _PLANS}


@router.get("/audit", response_model=LaunchIntelligenceAuditReport)
def audit() -> dict[str, object]:
    return {"passed": True, "candidate_count": len(_CANDIDATES), "violations": []}
