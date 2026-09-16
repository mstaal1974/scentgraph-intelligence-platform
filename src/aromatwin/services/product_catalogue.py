"""Public-safe Maison product projection built from approved fragrance records."""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
APPROVED = {"approved", "approved_for_catalogue", "public_safe", "review_safe", "published"}
FORBIDDEN_PARTS = {
    "supplier_price",
    "supplier_cost",
    "supplier_code",
    "supplier_name",
    "cost",
    "margin",
    "cn_code",
    "stock",
    "quantity",
    "price_aed",
    "price_usd",
    "commercial_terms",
    "third_party_description",
    "reviews",
    "rating",
    "image",
    "comment",
    "ugc",
}


def slugify(value: object) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", str(value).lower()))


def tokens(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value or "").replace("|", ",").split(",") if part.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def is_approved(row: Mapping[str, object]) -> bool:
    explicit = row.get("approved", row.get("public_approved"))
    if explicit not in (None, "") and str(explicit).lower() not in {"1", "true", "yes", "approved"}:
        return False
    status = str(row.get("review_status") or row.get("approval_status") or "approved").lower()
    return status in APPROVED and not any(
        value not in (None, "", [], {})
        and any(part in str(key).lower() for part in FORBIDDEN_PARTS)
        for key, value in row.items()
    )


class ProductCatalogueService:
    """Creates a strict, allowlisted product view; input dictionaries are never passed through."""

    def __init__(
        self,
        catalogue: Iterable[Mapping[str, object]] | None = None,
        vectors: Iterable[Mapping[str, object]] | None = None,
        recommendations: Iterable[Mapping[str, object]] | None = None,
        *,
        data_dir: Path = DATA_DIR,
    ) -> None:
        self.catalogue = (
            list(catalogue)
            if catalogue is not None
            else read_csv(data_dir / "catalogue_fragrances.csv")
        )
        self.vectors = (
            list(vectors) if vectors is not None else read_csv(data_dir / "scent_vectors.csv")
        )
        self.recommendations = (
            list(recommendations)
            if recommendations is not None
            else read_csv(data_dir / "recommendations.csv")
        )
        self.rejected_count = 0

    def build(self) -> list[dict[str, object]]:
        products: dict[str, dict[str, object]] = {}
        self.rejected_count = 0
        for row in self.catalogue:
            if not is_approved(row):
                self.rejected_count += 1
                continue
            fragrance_id = str(row.get("fragrance_id") or row.get("id") or "").strip()
            if not fragrance_id:
                self.rejected_count += 1
                continue
            brand = str(row.get("brand_name") or row.get("brand") or "Maison Obsidian").strip()
            fragrance = str(
                row.get("fragrance_name") or row.get("name") or row.get("title") or ""
            ).strip()
            if not fragrance:
                self.rejected_count += 1
                continue
            key = fragrance_id
            if key in products:
                continue
            vector = next(
                (
                    v
                    for v in self.vectors
                    if str(v.get("fragrance_id")) == fragrance_id
                    and str(v.get("review_status", "")).lower() in APPROVED
                ),
                {},
            )
            family = str(row.get("product_family") or row.get("family") or "signature fragrance")
            accords = tokens(row.get("accords") or vector.get("accords"))
            top = tokens(row.get("top_notes"))
            heart = tokens(row.get("heart_notes"))
            base = tokens(row.get("base_notes"))
            moods = tokens(row.get("moods") or row.get("mood"))
            occasions = tokens(row.get("occasions") or row.get("occasion"))
            seasons = tokens(row.get("seasons") or row.get("season"))
            scent_terms = accords or top + heart + base or [family]
            scent_summary = f"A {family.lower()} profile shaped by {', '.join(scent_terms[:3])}."
            description = (
                f"Meet {fragrance}, a Maison composition with a {family.lower()} character. "
                f"Its profile is designed to feel {', '.join(moods[:2]).lower() or 'distinctive and balanced'}."
            )
            now = str(
                row.get("updated_at") or row.get("created_at") or datetime.now(UTC).isoformat()
            )
            product_slug = slugify(f"{brand}-{fragrance}")
            products[key] = {
                "product_id": "prd_" + hashlib.sha256(key.encode()).hexdigest()[:12],
                "fragrance_id": fragrance_id,
                "brand_name": brand,
                "fragrance_name": fragrance,
                "product_title": f"{brand} {fragrance}",
                "product_slug": product_slug,
                "product_family": family,
                "scent_summary": scent_summary,
                "public_description_original": description,
                "top_notes": top,
                "heart_notes": heart,
                "base_notes": base,
                "accords": accords,
                "moods": moods,
                "occasions": occasions,
                "seasons": seasons,
                "tags": sorted(
                    set(slugify(item) for item in scent_terms + moods + occasions + seasons if item)
                ),
                "review_status": "approved",
                "publication_status": str(row.get("publication_status") or "published"),
                "created_at": str(row.get("created_at") or now),
                "updated_at": now,
            }
        return list(products.values())
