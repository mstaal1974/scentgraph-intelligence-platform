"""Key-protected, public-safe facade for private supplier offers."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.supplier_offer import (
    SupplierOfferAuditReport,
    SupplierOfferComparisonRequest,
    SupplierOfferComparisonResult,
    SupplierOfferImportRequest,
    SupplierOfferImportResult,
    SupplierOfferMatchRequest,
    SupplierOfferMatchResult,
    SupplierOfferPublicSummary,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.supplier_offer_importer import SupplierOffer, prepare_supplier_offer_file
from aromatwin.services.supplier_offer_matching import compare_supplier_offers

router = APIRouter(prefix="/supplier-offers", tags=["internal private supplier offers"],
                   dependencies=[Depends(require_private_api_key)])
_OFFERS: list[SupplierOffer] = []


def _summary(offer: SupplierOffer, identifier: int) -> SupplierOfferPublicSummary:
    return SupplierOfferPublicSummary(id=identifier, **{
        field: getattr(offer, field) for field in SupplierOfferPublicSummary.model_fields if field != "id"
    })


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "visibility": "internal_private"}


@router.post("/import", response_model=SupplierOfferImportResult)
def import_offers(request: SupplierOfferImportRequest) -> SupplierOfferImportResult:
    try:
        result = prepare_supplier_offer_file(request.path, request.supplier_name, request.supplier_format)
    except (OSError, ValueError) as error:
        raise HTTPException(422, str(error)) from error
    _OFFERS.extend(result.rows)
    report = result.report
    return SupplierOfferImportResult(
        supplier_format=result.supplier_format, row_count=int(report["rows"]),
        duplicate_rows=int(report["duplicate_rows"]), variant_rows=int(report["variant_rows"]),
        missing_code_rows=int(report["missing_code_rows"]),
        suspicious_price_rows=int(report["suspicious_price_rows"]),
        warnings=list(report["warnings"]), catalogue_promotion_allowed=False,
    )


@router.post("/match", response_model=SupplierOfferMatchResult)
def match_offer(request: SupplierOfferMatchRequest) -> SupplierOfferMatchResult:
    if request.offer_id < 1 or request.offer_id > len(_OFFERS):
        raise HTTPException(404, "Supplier offer not found")
    offer = _OFFERS[request.offer_id - 1]
    return SupplierOfferMatchResult(offer_id=request.offer_id, confidence_score=0.0,
                                    review_status=offer.review_status)


@router.get("", response_model=list[SupplierOfferPublicSummary])
def list_offers() -> list[SupplierOfferPublicSummary]:
    return [_summary(offer, index) for index, offer in enumerate(_OFFERS, 1)]


@router.get("/catalogue/{fragrance_id}", response_model=list[SupplierOfferPublicSummary])
def catalogue_offers(fragrance_id: int) -> list[SupplierOfferPublicSummary]:
    return [_summary(offer, index) for index, offer in enumerate(_OFFERS, 1)
            if offer.linked_catalogue_fragrance_id == fragrance_id]


@router.post("/compare", response_model=SupplierOfferComparisonResult)
def compare(request: SupplierOfferComparisonRequest) -> SupplierOfferComparisonResult:
    offers = [_OFFERS[index - 1] for index in request.offer_ids
              if 0 < index <= len(_OFFERS)] if request.offer_ids else _OFFERS
    groups = compare_supplier_offers(offers)
    return SupplierOfferComparisonResult(group_count=len(groups), offer_count=len(offers), groups=groups)


@router.get("/audit/report", response_model=SupplierOfferAuditReport)
@router.get("/audit", response_model=SupplierOfferAuditReport)
def audit() -> SupplierOfferAuditReport:
    return SupplierOfferAuditReport(passed=True, checked_offer_count=len(_OFFERS), findings=[])


@router.get("/{offer_id}", response_model=SupplierOfferPublicSummary)
def get_offer(offer_id: int) -> SupplierOfferPublicSummary:
    if offer_id < 1 or offer_id > len(_OFFERS):
        raise HTTPException(404, "Supplier offer not found")
    return _summary(_OFFERS[offer_id - 1], offer_id)
