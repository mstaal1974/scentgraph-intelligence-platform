"""Schemas for the key-protected sourcing boundary."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SupplierSourcingDecisionRead(BaseModel):
    id: str
    catalogue_fragrance_id: int | None = None
    match_candidate_id: int | None = None
    fragrance_title: str
    availability_status: str
    sourcing_recommendation: str
    risk_flags: list[str]
    review_status: str
    confidence_score: float = Field(ge=0, le=1)
    public_safe_summary: str
    created_at: datetime
    updated_at: datetime


class SupplierSourcingDecisionPrivateRead(SupplierSourcingDecisionRead):
    """Explicit private representation; never used as a default route response."""
    supplier_name: str
    supplier_offer_id: str
    supplier_match_confidence: float
    supplier_price_confidence: float
    price_basis: str | None = None
    internal_rank: int
    sourcing_reason: str
    supplier_price_private: Decimal | None = None
    supplier_code_private: str | None = None
    supplier_cn_code_private: str | None = None
    quantity_private: Decimal | None = None


class SupplierSourcingRequest(BaseModel):
    private_offer_path: str


class SupplierSourcingResult(BaseModel):
    accepted_count: int
    rejected_count: int
    decisions: list[SupplierSourcingDecisionRead]
    contains_commercial_fields: bool = False


class SupplierComparisonRequest(BaseModel):
    decision_ids: list[str] = []


class SupplierComparisonResult(BaseModel):
    group_count: int
    candidate_count: int
    summaries: list[SupplierSourcingDecisionRead]
    contains_commercial_fields: bool = False


class ProductFormatCostInput(BaseModel):
    product_format: str
    fragrance_oil_cost: Decimal = Field(ge=0)
    bottle_cost: Decimal = Field(default=Decimal("0"), ge=0)
    cap_sprayer_cost: Decimal = Field(default=Decimal("0"), ge=0)
    label_cost: Decimal = Field(default=Decimal("0"), ge=0)
    box_packaging_cost: Decimal = Field(default=Decimal("0"), ge=0)
    labour_cost: Decimal = Field(default=Decimal("0"), ge=0)
    wastage_percentage: Decimal = Field(default=Decimal("0"), ge=0)
    fulfilment_cost: Decimal = Field(default=Decimal("0"), ge=0)
    marketplace_fee: Decimal = Field(default=Decimal("0"), ge=0)
    payment_processing_fee: Decimal = Field(default=Decimal("0"), ge=0)
    referral_fee: Decimal = Field(default=Decimal("0"), ge=0)
    gst_tax_placeholder: Decimal = Field(default=Decimal("0"), ge=0)
    target_margin_percentage: Decimal = Field(default=Decimal("60"), ge=0, lt=100)
    fill_volume_ml: Decimal | None = Field(default=None, ge=0)
    oil_concentration_percentage: Decimal = Field(default=Decimal("20"), ge=0, le=100)


class ProductFormatMarginResult(BaseModel):
    product_format: str
    fill_volume_ml: Decimal | None
    oil_cost_estimate: Decimal
    packaging_cost_estimate: Decimal
    labour_cost_estimate: Decimal
    total_unit_cost_estimate: Decimal
    suggested_retail_price: Decimal
    gross_margin_amount: Decimal
    gross_margin_percentage: Decimal
    scenario_name: str
    confidence_score: float
    private_notes: str | None
    review_status: str


class MarginScenarioRequest(BaseModel):
    scenario_name: str = "target"
    inputs: list[ProductFormatCostInput]


class MarginScenarioPublicResult(BaseModel):
    product_format: str
    scenario_name: str
    review_status: str
    confidence_score: float
    public_safe_summary: str


class MarginScenarioResult(BaseModel):
    accepted_count: int
    rejected_count: int
    scenarios: list[MarginScenarioPublicResult]
    contains_commercial_fields: bool = False


class SourcingAuditReport(BaseModel):
    passed: bool
    checked_offer_count: int
    duplicate_offer_count: int
    missing_code_count: int
    suspicious_price_count: int
    low_confidence_count: int
