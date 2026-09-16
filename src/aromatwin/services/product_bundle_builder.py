"""Original public-safe product bundle generation."""

from __future__ import annotations

import hashlib
from typing import Iterable, Mapping

from aromatwin.services.product_catalogue import slugify

BUNDLE_TYPES = (
    "discovery_kit",
    "mood_kit",
    "season_kit",
    "occasion_kit",
    "note_family_kit",
    "car_diffuser_kit",
    "body_care_layering_kit",
    "inspired_by_collection_kit",
)


class ProductBundleBuilder:
    def build(
        self, products: Iterable[Mapping[str, object]], variants: Iterable[Mapping[str, object]]
    ) -> list[dict[str, object]]:
        products, variants = list(products), list(variants)
        if not products:
            return []
        output = []
        for bundle_type in BUNDLE_TYPES:
            selected = products[: min(3, len(products))]
            product_ids = [str(item["product_id"]) for item in selected]
            eligible = {
                "car_diffuser_kit": {"car_diffuser"},
                "body_care_layering_kit": {"body_wash", "moisturiser"},
                "discovery_kit": {"10ml_tester"},
            }.get(bundle_type, {"10ml_tester", "30ml_bottle"})
            variant_ids = [
                str(item["variant_id"])
                for item in variants
                if item.get("product_id") in product_ids and item.get("product_format") in eligible
            ][:6]
            theme = bundle_type.replace("_kit", "").replace("_", " ").title()
            slug = slugify(f"maison {theme} kit")
            output.append(
                {
                    "bundle_id": "bnd_" + hashlib.sha256(bundle_type.encode()).hexdigest()[:12],
                    "bundle_title": f"Maison {theme} Kit",
                    "bundle_slug": slug,
                    "bundle_type": bundle_type,
                    "included_product_ids": product_ids,
                    "included_variant_ids": variant_ids,
                    "public_bundle_description": f"Explore a curated {theme.lower()} selection of complementary Maison scent profiles.",
                    "scent_theme": theme,
                    "tags": [slugify(theme), "maison-kit"],
                    "review_status": "approved",
                    "publication_status": "published",
                }
            )
        return output
