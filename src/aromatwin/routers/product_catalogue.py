"""Maison product endpoints with separate public and internal workflow boundaries."""

from fastapi import APIRouter, Depends, HTTPException

from aromatwin.schemas.product_catalogue import (
    ProductBundleBuildRequest,
    ProductBundleBuildResult,
    ProductBundlePublicRead,
    ProductCatalogueBuildRequest,
    ProductCatalogueBuildResult,
    ProductCataloguePublicRead,
    ProductVariantBuildRequest,
    ProductVariantBuildResult,
    ProductVariantPublicRead,
)
from aromatwin.security import optional_public_api_key, require_admin_api_key
from aromatwin.services.product_bundle_builder import ProductBundleBuilder
from aromatwin.services.product_catalogue import ProductCatalogueService
from aromatwin.services.product_variant_builder import ProductVariantBuilder

router = APIRouter(prefix="/products", tags=["products"])
SERVICE = ProductCatalogueService()
PRODUCTS = SERVICE.build()
VARIANTS = ProductVariantBuilder().build(PRODUCTS)
BUNDLES = ProductBundleBuilder().build(PRODUCTS, VARIANTS)


def _public(row: dict[str, object], schema: type) -> object:
    return schema.model_validate(row)


@router.get("/health", dependencies=[Depends(optional_public_api_key)])
def health() -> dict[str, object]:
    return {"status": "ok", "service": "maison-product-catalogue", "product_count": len(PRODUCTS)}


@router.post(
    "/build",
    response_model=ProductCatalogueBuildResult,
    dependencies=[Depends(require_admin_api_key)],
)
def build_products(request: ProductCatalogueBuildRequest) -> dict[str, object]:
    global PRODUCTS, VARIANTS, BUNDLES
    PRODUCTS = SERVICE.build()
    if request.include_variants:
        VARIANTS = ProductVariantBuilder().build(PRODUCTS)
    if request.include_default_bundles:
        BUNDLES = ProductBundleBuilder().build(PRODUCTS, VARIANTS)
    return {
        "accepted_count": len(PRODUCTS),
        "rejected_count": SERVICE.rejected_count,
        "products": PRODUCTS,
    }


@router.get(
    "",
    response_model=list[ProductCataloguePublicRead],
    dependencies=[Depends(optional_public_api_key)],
)
def products() -> list[object]:
    return [_public(item, ProductCataloguePublicRead) for item in PRODUCTS]


@router.get(
    "/slug/{product_slug}",
    response_model=ProductCataloguePublicRead,
    dependencies=[Depends(optional_public_api_key)],
)
def product_by_slug(product_slug: str) -> object:
    row = next((item for item in PRODUCTS if item["product_slug"] == product_slug), None)
    if row is None:
        raise HTTPException(404, "Published product not found")
    return _public(row, ProductCataloguePublicRead)


@router.post(
    "/variants/build",
    response_model=ProductVariantBuildResult,
    dependencies=[Depends(require_admin_api_key)],
)
def build_variants(request: ProductVariantBuildRequest) -> dict[str, object]:
    global VARIANTS
    chosen = [
        p for p in PRODUCTS if not request.product_ids or p["product_id"] in request.product_ids
    ]
    VARIANTS = ProductVariantBuilder().build(chosen, request.formats or None, request.public_prices)
    return {"accepted_count": len(VARIANTS), "rejected_count": 0, "variants": VARIANTS}


@router.get(
    "/bundles",
    response_model=list[ProductBundlePublicRead],
    dependencies=[Depends(optional_public_api_key)],
)
def bundles() -> list[object]:
    return [_public(item, ProductBundlePublicRead) for item in BUNDLES]


@router.post(
    "/bundles/build",
    response_model=ProductBundleBuildResult,
    dependencies=[Depends(require_admin_api_key)],
)
def build_bundles(request: ProductBundleBuildRequest) -> dict[str, object]:
    global BUNDLES
    chosen = [
        p for p in PRODUCTS if not request.product_ids or p["product_id"] in request.product_ids
    ]
    BUNDLES = ProductBundleBuilder().build(chosen, VARIANTS)
    return {"accepted_count": len(BUNDLES), "rejected_count": 0, "bundles": BUNDLES}


@router.get(
    "/bundles/{bundle_id}",
    response_model=ProductBundlePublicRead,
    dependencies=[Depends(optional_public_api_key)],
)
def bundle(bundle_id: str) -> object:
    row = next((item for item in BUNDLES if item["bundle_id"] == bundle_id), None)
    if row is None:
        raise HTTPException(404, "Published bundle not found")
    return _public(row, ProductBundlePublicRead)


@router.get(
    "/export/maison",
    response_model=list[ProductCataloguePublicRead],
    dependencies=[Depends(optional_public_api_key)],
)
def export_products() -> list[object]:
    return products()


@router.get(
    "/export/variants",
    response_model=list[ProductVariantPublicRead],
    dependencies=[Depends(optional_public_api_key)],
)
def export_variants() -> list[object]:
    return [_public(item, ProductVariantPublicRead) for item in VARIANTS]


@router.get(
    "/export/bundles",
    response_model=list[ProductBundlePublicRead],
    dependencies=[Depends(optional_public_api_key)],
)
def export_bundles() -> list[object]:
    return bundles()


@router.get(
    "/{product_id}/variants",
    response_model=list[ProductVariantPublicRead],
    dependencies=[Depends(optional_public_api_key)],
)
def product_variants(product_id: str) -> list[object]:
    if not any(item["product_id"] == product_id for item in PRODUCTS):
        raise HTTPException(404, "Published product not found")
    return [
        _public(item, ProductVariantPublicRead)
        for item in VARIANTS
        if item["product_id"] == product_id
    ]


@router.get(
    "/{product_id}",
    response_model=ProductCataloguePublicRead,
    dependencies=[Depends(optional_public_api_key)],
)
def product(product_id: str) -> object:
    row = next((item for item in PRODUCTS if item["product_id"] == product_id), None)
    if row is None:
        raise HTTPException(404, "Published product not found")
    return _public(row, ProductCataloguePublicRead)
