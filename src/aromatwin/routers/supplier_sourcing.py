"""Key-protected supplier sourcing endpoints with safe-by-default responses."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.supplier_sourcing import (
    MarginScenarioRequest,
    MarginScenarioResult,
    SourcingAuditReport,
    SupplierComparisonRequest,
    SupplierComparisonResult,
    SupplierSourcingDecisionRead,
    SupplierSourcingRequest,
    SupplierSourcingResult,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.margin_intelligence import CostInput, calculate_margin, public_safe_margin
from aromatwin.services.supplier_sourcing import (
    SourcingDecision,
    audit_offers,
    build_sourcing_decisions,
    load_private_supplier_offers,
    public_safe_decision,
)

router = APIRouter(prefix="/supplier-sourcing", tags=["internal private supplier sourcing"],
                   dependencies=[Depends(require_private_api_key)])
_OFFERS = []
_DECISIONS: list[SourcingDecision] = []


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.post("/build", response_model=SupplierSourcingResult)
def build(request: SupplierSourcingRequest) -> SupplierSourcingResult:
    try:
        offers = load_private_supplier_offers(request.private_offer_path)
    except (OSError, ValueError) as error:
        raise HTTPException(422, str(error)) from error
    decisions = build_sourcing_decisions(offers)
    _OFFERS[:] = offers
    _DECISIONS[:] = decisions
    accepted = sum(d.sourcing_recommendation == "preferred_candidate" for d in decisions)
    return SupplierSourcingResult(accepted_count=accepted, rejected_count=len(decisions) - accepted,
                                  decisions=[public_safe_decision(d) for d in decisions])


@router.post("/compare", response_model=SupplierComparisonResult)
def compare(request: SupplierComparisonRequest) -> SupplierComparisonResult:
    selected = [d for d in _DECISIONS if not request.decision_ids or d.id in request.decision_ids]
    group_count = len({(d.catalogue_fragrance_id, d.match_candidate_id, d.fragrance_title) for d in selected})
    return SupplierComparisonResult(group_count=group_count, candidate_count=len(selected),
                                    summaries=[public_safe_decision(d) for d in selected])


@router.get("/decisions", response_model=list[SupplierSourcingDecisionRead])
def decisions() -> list[dict[str, object]]:
    return [public_safe_decision(d) for d in _DECISIONS]


@router.get("/decisions/{decision_id}", response_model=SupplierSourcingDecisionRead)
def decision(decision_id: str) -> dict[str, object]:
    found = next((d for d in _DECISIONS if d.id == decision_id), None)
    if found is None:
        raise HTTPException(404, "Sourcing decision not found")
    return public_safe_decision(found)


@router.post("/margin-scenarios", response_model=MarginScenarioResult)
def margin_scenarios(request: MarginScenarioRequest) -> MarginScenarioResult:
    scenarios = [calculate_margin(CostInput(**item.model_dump()), request.scenario_name)
                 for item in request.inputs]
    return MarginScenarioResult(accepted_count=len(scenarios), rejected_count=0,
                                scenarios=[public_safe_margin(item) for item in scenarios])


@router.get("/audit", response_model=SourcingAuditReport)
def audit() -> dict[str, int | bool]:
    return audit_offers(_OFFERS)
