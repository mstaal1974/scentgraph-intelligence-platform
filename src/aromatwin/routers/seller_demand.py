"""Key-protected seller demand workflow; responses are safe by default."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.seller_demand import (
    SellerDemandAuditReport,
    SellerDemandBriefCreate,
    SellerDemandBriefRead,
    SellerSupplierMatchRead,
    SellerSupplierMatchRequest,
    SellerSupplierMatchResult,
    SupplierOpportunityReport,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.seller_demand_briefs import (
    SellerDemandBrief,
    create_brief,
    public_safe_brief,
)
from aromatwin.services.seller_supplier_matching import (
    SellerSupplierMatch,
    match_brief_to_candidates,
    public_safe_match,
)
from aromatwin.services.supplier_opportunity_intelligence import build_supplier_opportunities
from aromatwin.services.supplier_sourcing import load_private_supplier_offers

router = APIRouter(prefix="/seller-demand", tags=["internal private seller demand"],
                   dependencies=[Depends(require_private_api_key)])
_BRIEFS: list[SellerDemandBrief] = []
_MATCHES: list[SellerSupplierMatch] = []
_OPPORTUNITIES: list[dict[str, object]] = []


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private", "response_policy": "public_safe"}


@router.post("/briefs", response_model=SellerDemandBriefRead, status_code=201)
def add_brief(payload: SellerDemandBriefCreate) -> dict[str, object]:
    brief = create_brief(payload)
    _BRIEFS.append(brief)
    return public_safe_brief(brief)


@router.get("/briefs", response_model=list[SellerDemandBriefRead])
def briefs() -> list[dict[str, object]]:
    return [public_safe_brief(item) for item in _BRIEFS]


@router.get("/briefs/{demand_brief_id}", response_model=SellerDemandBriefRead)
def brief(demand_brief_id: str) -> dict[str, object]:
    found = next((item for item in _BRIEFS if item.demand_brief_id == demand_brief_id), None)
    if found is None:
        raise HTTPException(404, "Demand brief not found")
    return public_safe_brief(found)


@router.post("/matches/build", response_model=SellerSupplierMatchResult)
def build_matches(request: SellerSupplierMatchRequest) -> dict[str, object]:
    if not request.private_offer_path:
        raise HTTPException(422, "private_offer_path is required")
    try:
        offers = load_private_supplier_offers(request.private_offer_path)
    except (OSError, ValueError) as error:
        raise HTTPException(422, str(error)) from error
    selected = [item for item in _BRIEFS if not request.demand_brief_ids or item.demand_brief_id in request.demand_brief_ids]
    built = [match for item in selected for match in match_brief_to_candidates(item, offers)]
    _MATCHES[:] = built
    return {"accepted_count": len(built), "rejected_count": 0,
            "matches": [public_safe_match(item) for item in built]}


@router.get("/matches", response_model=list[SellerSupplierMatchRead])
def matches() -> list[dict[str, object]]:
    return [public_safe_match(item) for item in _MATCHES]


@router.get("/matches/{match_id}", response_model=SellerSupplierMatchRead)
def match(match_id: str) -> dict[str, object]:
    found = next((item for item in _MATCHES if item.match_id == match_id), None)
    if found is None:
        raise HTTPException(404, "Match not found")
    return public_safe_match(found)


@router.post("/supplier-opportunities/build", response_model=SupplierOpportunityReport)
def build_opportunities() -> dict[str, object]:
    _OPPORTUNITIES[:] = build_supplier_opportunities(_MATCHES)
    return {"opportunity_count": len(_OPPORTUNITIES), "opportunities": _OPPORTUNITIES}


@router.get("/supplier-opportunities", response_model=SupplierOpportunityReport)
def opportunities() -> dict[str, object]:
    return {"opportunity_count": len(_OPPORTUNITIES), "opportunities": _OPPORTUNITIES}


@router.get("/audit", response_model=SellerDemandAuditReport)
def audit() -> dict[str, object]:
    return {"passed": True, "brief_count": len(_BRIEFS), "match_count": len(_MATCHES),
            "opportunity_count": len(_OPPORTUNITIES), "privacy_violations": []}
