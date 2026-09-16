"""Guarded promotion of approved enrichment reviews into public catalogue records."""

import csv
import re
import unicodedata
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Mapping, Sequence

APPROVED_FOR_CATALOGUE = "approved_for_catalogue"
DEFAULT_CONFIDENCE_THRESHOLD = 0.75

PRIVATE_SUPPLIER_FIELDS = frozenset(
    {
        "supplier_price", "aed_price", "usd_price", "price", "supplier_code",
        "supplier_cn_code", "cn_code", "stock", "quantity", "commercial_terms",
        "supplier_commercial_terms",
    }
)
RESTRICTED_CONTENT_FIELDS = frozenset(
    {"description", "third_party_description", "review", "reviews", "rating", "ratings", "image",
     "image_url", "comment", "comments", "ugc"}
)
CATALOGUE_FIELDS = (
    "id", "brand_id", "brand", "brand_slug", "name", "slug", "concentration",
    "description", "source_confidence", "provenance_summary", "provenance_references",
    "enrichment_review_id",
)


@dataclass(frozen=True)
class CatalogueFragrance:
    id: int
    brand_id: int
    brand: str
    brand_slug: str
    name: str
    slug: str
    concentration: str | None
    description: str
    source_confidence: float
    provenance_summary: str
    provenance_references: tuple[int, ...]
    enrichment_review_id: int


def slugify(value: str) -> str:
    """Return a deterministic, URL-safe ASCII slug."""
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def _values(review: object) -> Mapping[str, object]:
    if isinstance(review, Mapping):
        return review
    if is_dataclass(review):
        return asdict(review)
    return vars(review)


def _has_value(data: Mapping[str, object], fields: frozenset[str]) -> bool:
    return any(data.get(field) not in (None, "", False, (), [], {}) for field in fields)


def validate_review_for_promotion(
    review: object, *, confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> Mapping[str, object]:
    """Validate that *review* has crossed every catalogue publication gate."""
    data = _values(review)
    if data.get("review_status") != APPROVED_FOR_CATALOGUE:
        raise ValueError("Only approved_for_catalogue enrichment reviews can be promoted")
    if str(data.get("record_type", "enrichment_review")) != "enrichment_review" or not {
        "profile_draft_id", "description_original", "copied_restricted_content"
    }.issubset(data):
        raise ValueError("Only enrichment reviews can be promoted")
    if float(data.get("source_confidence") or 0) < confidence_threshold:
        raise ValueError("Source confidence is below the catalogue promotion threshold")
    if str(data.get("licensing_risk", "")).strip().lower() == "high":
        raise ValueError("High licensing risk prevents catalogue promotion")
    if str(data.get("copied_restricted_content", "false")).strip().lower() in {"true", "1"}:
        raise ValueError("Copied restricted content prevents catalogue promotion")
    if _has_value(data, RESTRICTED_CONTENT_FIELDS):
        raise ValueError("Restricted third-party content prevents catalogue promotion")
    if _has_value(data, PRIVATE_SUPPLIER_FIELDS):
        raise ValueError("Supplier-private fields cannot be exposed by catalogue promotion")
    references = data.get("source_ids") or data.get("provenance_references")
    if not references or not _source_ids(references) or not str(
        data.get("provenance_summary", "")
    ).strip():
        raise ValueError("Sufficient provenance is required for catalogue promotion")
    if not str(data.get("reviewer", "")).strip():
        raise ValueError("Human reviewer attribution is required for catalogue promotion")
    if not str(data.get("brand", "")).strip() or not str(
        data.get("fragrance_name", data.get("name", ""))
    ).strip():
        raise ValueError("Brand and fragrance name are required")
    return data


def _source_ids(value: object) -> tuple[int, ...]:
    if isinstance(value, str):
        return tuple(int(item) for item in re.findall(r"\d+", value))
    return tuple(int(item) for item in value)  # type: ignore[arg-type]


def promote_enrichment_review(
    review: object,
    existing: Sequence[CatalogueFragrance] = (),
    *,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> CatalogueFragrance:
    """Create a public allowlisted record, or return the prior idempotent promotion."""
    data = validate_review_for_promotion(review, confidence_threshold=confidence_threshold)
    review_id = int(data["id"])
    prior = next((item for item in existing if item.enrichment_review_id == review_id), None)
    if prior is not None:
        return prior

    brand = str(data["brand"]).strip()
    name = str(data.get("fragrance_name", data.get("name"))).strip()
    brand_slug = slugify(brand)
    duplicate = next(
        (item for item in existing if item.brand_slug == brand_slug and item.slug == slugify(name)),
        None,
    )
    if duplicate is not None:
        raise ValueError("A catalogue fragrance with this brand and name already exists")
    brands = {item.brand_slug: item.brand_id for item in existing}
    brand_id = brands.get(brand_slug, max(brands.values(), default=0) + 1)
    return CatalogueFragrance(
        id=max((item.id for item in existing), default=0) + 1,
        brand_id=brand_id,
        brand=brand,
        brand_slug=brand_slug,
        name=name,
        slug=slugify(name),
        concentration=str(data.get("concentration") or "") or None,
        description=str(data.get("description_original") or "").strip(),
        source_confidence=float(data["source_confidence"]),
        provenance_summary=str(data["provenance_summary"]).strip(),
        provenance_references=_source_ids(data.get("source_ids")),
        enrichment_review_id=review_id,
    )


def load_approved_enrichment_reviews(path: Path) -> list[dict[str, object]]:
    """Load only approved reviews; validation remains the promoter's responsibility."""
    with path.open(newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    return [row for row in rows if row.get("review_status") == APPROVED_FOR_CATALOGUE]


def write_catalogue_csv(path: Path, records: Sequence[CatalogueFragrance]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=CATALOGUE_FIELDS)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["provenance_references"] = "|".join(map(str, record.provenance_references))
            writer.writerow(row)
