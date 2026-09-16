from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SupplierItemFields(BaseModel):
    supplier_name: str
    supplier_brand_raw: str
    supplier_name_raw: str
    supplier_ori_raw: str | None = None
    supplier_cn_code: str | None = None
    quantity: Decimal | None = Field(default=None, ge=0)
    aed_price: Decimal | None = Field(default=None, ge=0)
    usd_price: Decimal | None = Field(default=None, ge=0)
    source_file: str
    source_row_number: int = Field(ge=1)
    normalised_brand: str
    normalised_name: str
    variant_marker: str | None = None
    status: str


class SupplierItemRead(SupplierItemFields):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SupplierItemPreview(SupplierItemFields):
    model_config = ConfigDict(from_attributes=True)
    is_duplicate: bool


class SupplierImportPreviewRequest(BaseModel):
    supplier_name: str = Field(min_length=1)
    source_file: str = Field(default="api-preview.csv", min_length=1)
    rows: list[dict[str, object]] = Field(min_length=1)


class SupplierImportPreviewResponse(BaseModel):
    rows: list[SupplierItemPreview]
    row_count: int
    duplicate_rows: int
    variant_rows: int
    status: str
    catalogue_promotion_allowed: bool
    warnings: list[str]
