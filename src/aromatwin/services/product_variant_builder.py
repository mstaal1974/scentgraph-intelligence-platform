"""Deterministic, public-safe Maison product variant generation."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Iterable, Mapping

from aromatwin.services.product_catalogue import slugify

FORMAT_CONFIG = {
    "10ml_tester": ("10ml tester", 10),
    "30ml_bottle": ("30ml bottle", 30),
    "50ml_bottle": ("50ml bottle", 50),
    "car_diffuser": ("car diffuser", 8),
    "body_wash": ("body wash", 250),
    "moisturiser": ("moisturiser", 250),
    "kit_bundle": ("kit / bundle", None),
}


class ProductVariantBuilder:
    def build(
        self,
        products: Iterable[Mapping[str, object]],
        formats: Iterable[str] | None = None,
        public_prices: Mapping[str, Decimal | float | str] | None = None,
    ) -> list[dict[str, object]]:
        output = []
        formats = list(formats or FORMAT_CONFIG)
        prices = public_prices or {}
        for product in products:
            for product_format in formats:
                if product_format not in FORMAT_CONFIG:
                    continue
                size, volume = FORMAT_CONFIG[product_format]
                sku = "MAISON-{}-{}-{}".format(
                    slugify(product.get("brand_name", "maison")).upper(),
                    slugify(product.get("fragrance_name", product["product_id"])).upper(),
                    product_format.replace("_", "-").upper(),
                )
                output.append(
                    {
                        "variant_id": "var_" + hashlib.sha256(sku.encode()).hexdigest()[:12],
                        "product_id": product["product_id"],
                        "product_format": product_format,
                        "size_label": size,
                        "fill_volume_ml": volume,
                        "sku": sku,
                        "barcode_placeholder": None,
                        "retail_price_public": str(prices[product_format])
                        if product_format in prices
                        else None,
                        "compare_at_price_public": None,
                        "inventory_policy": "continue",
                        "public_variant_description": f"{product['product_title']} in the {size} format.",
                        "review_status": "approved",
                        "publication_status": "published",
                    }
                )
        return output
