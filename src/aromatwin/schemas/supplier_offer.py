from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SupplierOfferPublicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int | None = None
    supplier_name: str
    normalised_brand: str
    normalised_name: str
    candidate_brand: str | None = None
    candidate_fragrance_name: str | None = None
    linked_match_candidate_id: int | None = None
    linked_catalogue_fragrance_id: int | None = None
    offer_status: str
    confidence_score: float | None = None
    review_status: str


class SupplierOfferRead(SupplierOfferPublicSummary):
    """Default allowlisted representation (intentionally contains no commercial fields)."""


class SupplierOfferPrivateRead(SupplierOfferPublicSummary):
    supplier_file_reference: str
    supplier_file_hash: str
    supplier_row_number: int
    supplier_brand_raw: str
    supplier_name_raw: str
    supplier_reference_raw: str | None = None
    supplier_code_private: str | None = None
    supplier_cn_code_private: str | None = None
    supplier_unit: str | None = None
    quantity_private: Decimal | None = None
    price_aed_private: Decimal | None = None
    price_usd_private: Decimal | None = None
    currency: str | None = None
    price_basis: str | None = None
    private_notes: str | None = None


class SupplierOfferImportRequest(BaseModel):
    path: str
    supplier_name: str
    supplier_format: str = "auto"


class SupplierOfferImportResult(BaseModel):
    supplier_format: str
    row_count: int
    duplicate_rows: int
    variant_rows: int
    missing_code_rows: int
    suspicious_price_rows: int
    warnings: list[str]
    report_reference: str | None = None
    catalogue_promotion_allowed: bool = False


class SupplierOfferMatchRequest(BaseModel):
    offer_id: int


class SupplierOfferMatchResult(BaseModel):
    offer_id: int
    matched_type: str | None = None
    matched_id: int | None = None
    confidence_score: float = Field(ge=0, le=1)
    review_status: str
    created_public_record: bool = False


class SupplierOfferComparisonRequest(BaseModel):
    offer_ids: list[int] = []


class SupplierOfferComparisonResult(BaseModel):
    group_count: int
    offer_count: int
    groups: list[dict[str, object]]
    contains_commercial_fields: bool = False


class SupplierOfferAuditReport(BaseModel):
    passed: bool
    checked_offer_count: int
    findings: list[str]
