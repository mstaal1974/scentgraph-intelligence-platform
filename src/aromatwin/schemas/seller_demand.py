"""Contracts for the internal, privacy-preserving demand matching workflow."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ProductFormat = Literal["10ml tester", "30ml bottle", "50ml bottle", "car diffuser", "body wash", "moisturiser", "kit / bundle"]


class SellerDemandBriefCreate(BaseModel):
    seller_name: str = Field(min_length=1)
    seller_segment: str = Field(min_length=1)
    target_customer: str = Field(min_length=1)
    desired_fragrance_families: list[str] = []
    desired_notes: list[str] = []
    desired_accords: list[str] = []
    desired_moods: list[str] = []
    desired_occasions: list[str] = []
    desired_seasons: list[str] = []
    desired_intensity: str | None = None
    desired_projection: str | None = None
    desired_longevity: str | None = None
    inspired_by_targets: list[str] = []
    product_formats: list[ProductFormat] = Field(min_length=1)
    target_public_price_band: str | None = None
    target_margin_band: Literal["low", "moderate", "strong", "unknown"] = "unknown"
    launch_quantity_band: str | None = None
    market_positioning: str | None = None
    urgency: str | None = None
    exclusions: list[str] = []
    private_seller_notes: str | None = None

    @field_validator("inspired_by_targets")
    @classmethod
    def trim_hints(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


class SellerDemandBriefUpdate(BaseModel):
    seller_segment: str | None = None
    target_customer: str | None = None
    desired_fragrance_families: list[str] | None = None
    desired_notes: list[str] | None = None
    desired_accords: list[str] | None = None
    desired_moods: list[str] | None = None
    desired_occasions: list[str] | None = None
    desired_seasons: list[str] | None = None
    desired_intensity: str | None = None
    desired_projection: str | None = None
    desired_longevity: str | None = None
    inspired_by_targets: list[str] | None = None
    product_formats: list[ProductFormat] | None = None
    target_public_price_band: str | None = None
    target_margin_band: Literal["low", "moderate", "strong", "unknown"] | None = None
    launch_quantity_band: str | None = None
    market_positioning: str | None = None
    urgency: str | None = None
    exclusions: list[str] | None = None
    private_seller_notes: str | None = None


class SellerDemandBriefRead(BaseModel):
    demand_brief_id: str
    seller_segment: str
    target_customer: str
    desired_fragrance_families: list[str]
    desired_notes: list[str]
    desired_accords: list[str]
    desired_moods: list[str]
    desired_occasions: list[str]
    desired_seasons: list[str]
    desired_intensity: str | None
    desired_projection: str | None
    desired_longevity: str | None
    inspired_by_targets: list[str]
    product_formats: list[ProductFormat]
    target_public_price_band: str | None
    target_margin_band: str
    launch_quantity_band: str | None
    market_positioning: str | None
    urgency: str | None
    exclusions: list[str]
    review_status: str
    created_at: datetime
    updated_at: datetime


class SellerDemandBriefPrivateRead(SellerDemandBriefRead):
    seller_name: str
    private_seller_notes: str | None = None


class SellerSupplierMatchRead(BaseModel):
    match_id: str
    demand_brief_id: str
    catalogue_fragrance_id: int | None = None
    match_candidate_id: int | None = None
    canonical_brand: str | None = None
    canonical_fragrance_name: str
    supplier_name_public_label: str
    scent_fit_score: float = Field(ge=0, le=1)
    commercial_fit_score: float = Field(ge=0, le=1)
    launch_readiness_score: float = Field(ge=0, le=1)
    overall_match_score: float = Field(ge=0, le=1)
    margin_suitability_band: Literal["low", "moderate", "strong", "unknown"]
    match_reasons: list[str]
    missing_requirements: list[str]
    risk_flags: list[str]
    next_action: str
    review_status: str
    created_at: datetime
    updated_at: datetime


class SellerSupplierMatchPrivateRead(SellerSupplierMatchRead):
    supplier_offer_id: str


class SellerSupplierMatchRequest(BaseModel):
    demand_brief_ids: list[str] = []
    private_offer_path: str | None = None


class SellerSupplierMatchResult(BaseModel):
    accepted_count: int
    rejected_count: int
    matches: list[SellerSupplierMatchRead]
    contains_sensitive_fields: bool = False


class SupplierOpportunityRead(BaseModel):
    supplier_opportunity_id: str
    supplier_name_public_label: str
    opportunity_theme: str
    matched_demand_count: int
    matched_format_count: int
    strongest_product_formats: list[str]
    strongest_fragrance_families: list[str]
    strongest_moods: list[str]
    strongest_occasions: list[str]
    strongest_seasons: list[str]
    catalogue_readiness_summary: str
    profile_gap_summary: str
    opportunity_score: float = Field(ge=0, le=1)
    opportunity_reason: str
    recommended_supplier_action: str
    review_status: str


class SupplierOpportunityPrivateRead(SupplierOpportunityRead):
    internal_supplier_reference: str


class SupplierOpportunityReport(BaseModel):
    opportunity_count: int
    opportunities: list[SupplierOpportunityRead]
    anonymised: bool = True


class SellerDemandAuditReport(BaseModel):
    passed: bool
    brief_count: int
    match_count: int
    opportunity_count: int
    privacy_violations: list[str]
