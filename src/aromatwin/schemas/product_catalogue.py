"""Allowlisted schemas for the Maison product SKU catalogue boundary."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCataloguePublicRead(BaseModel):
    product_id: str
    fragrance_id: str
    brand_name: str
    fragrance_name: str
    product_title: str
    product_slug: str
    product_family: str
    scent_summary: str
    public_description_original: str
    top_notes: list[str] = []
    heart_notes: list[str] = []
    base_notes: list[str] = []
    accords: list[str] = []
    moods: list[str] = []
    occasions: list[str] = []
    seasons: list[str] = []
    tags: list[str] = []
    publication_status: str


class ProductCatalogueRead(ProductCataloguePublicRead):
    review_status: str
    created_at: datetime
    updated_at: datetime


class ProductVariantPublicRead(BaseModel):
    variant_id: str
    product_id: str
    product_format: str
    size_label: str
    fill_volume_ml: int | None = None
    sku: str
    barcode_placeholder: str | None = None
    retail_price_public: Decimal | None = Field(default=None, ge=0)
    compare_at_price_public: Decimal | None = Field(default=None, ge=0)
    inventory_policy: str
    public_variant_description: str
    publication_status: str


class ProductVariantRead(ProductVariantPublicRead):
    review_status: str


class ProductBundlePublicRead(BaseModel):
    bundle_id: str
    bundle_title: str
    bundle_slug: str
    bundle_type: str
    included_product_ids: list[str]
    included_variant_ids: list[str]
    public_bundle_description: str
    scent_theme: str
    tags: list[str]
    publication_status: str


class ProductBundleRead(ProductBundlePublicRead):
    review_status: str


class ProductCatalogueBuildRequest(BaseModel):
    include_variants: bool = True
    include_default_bundles: bool = False


class ProductCatalogueBuildResult(BaseModel):
    accepted_count: int
    rejected_count: int
    products: list[ProductCatalogueRead]


class ProductVariantBuildRequest(BaseModel):
    product_ids: list[str] = []
    formats: list[str] = []
    public_prices: dict[str, Decimal] = {}


class ProductVariantBuildResult(BaseModel):
    accepted_count: int
    rejected_count: int
    variants: list[ProductVariantRead]


class ProductBundleBuildRequest(BaseModel):
    product_ids: list[str] = []


class ProductBundleBuildResult(BaseModel):
    accepted_count: int
    rejected_count: int
    bundles: list[ProductBundleRead]


class ProductExportRequest(BaseModel):
    publication_status: str = "published"


class ProductExportResult(BaseModel):
    export_type: str
    record_count: int
    records: list[dict[str, object]]
