"""Key-protected HTTP facade for the existing private supplier workflow."""

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.supplier_item import (
    SupplierImportPreviewRequest,
    SupplierImportPreviewResponse,
    SupplierItemPreview,
    SupplierItemRead,
)
from aromatwin.security import require_private_api_key
from aromatwin.services.supplier_importer import prepare_supplier_frame

router = APIRouter(
    prefix="/supplier-items",
    tags=["private supplier availability"],
    dependencies=[Depends(require_private_api_key)],
)
_ITEMS: list[SupplierItemRead] = []


@router.get("", response_model=list[SupplierItemRead])
def list_supplier_items() -> list[SupplierItemRead]:
    return _ITEMS


@router.get("/{item_id}", response_model=SupplierItemRead)
def get_supplier_item(item_id: int) -> SupplierItemRead:
    item = next((item for item in _ITEMS if item.id == item_id), None)
    if item is None:
        raise HTTPException(404, "Supplier item not found")
    return item


@router.post("/import-preview", response_model=SupplierImportPreviewResponse)
def import_preview(request: SupplierImportPreviewRequest) -> SupplierImportPreviewResponse:
    try:
        result = prepare_supplier_frame(
            pd.DataFrame(request.rows), request.supplier_name, request.source_file
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    report = result.report
    return SupplierImportPreviewResponse(
        rows=[SupplierItemPreview.model_validate(row) for row in result.rows],
        row_count=int(report["rows"]),
        duplicate_rows=int(report["duplicate_rows"]),
        variant_rows=int(report["variant_rows"]),
        status=str(report["status"]),
        catalogue_promotion_allowed=bool(report["catalogue_promotion_allowed"]),
        warnings=list(report["warnings"]),
    )
