"""Deterministic, public-safe scent vector generation and comparison."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from typing import Mapping, Sequence

from aromatwin.services.catalogue_promotion import (
    RESTRICTED_CONTENT_FIELDS,
    _present_supplier_private_fields,
)

VECTOR_DIMENSIONS = (
    "warm", "fresh", "sweet", "dark", "woody", "floral", "spicy", "fruity",
    "green", "aquatic", "marine", "leather", "powdery", "resinous", "smoky",
    "gourmand", "citrus", "aromatic", "amber", "musky", "luxury", "projection",
    "longevity",
)
# Reviewed classification carries far more signal than prose, so the two are weighted apart
# rather than concatenated into one bag of words.
STRUCTURED_SOURCE_FIELDS = ("family", "notes", "accords", "season", "occasion", "mood")
NARRATIVE_SOURCE_FIELDS = ("description_original", "description", "concentration")
PUBLIC_SOURCE_FIELDS = STRUCTURED_SOURCE_FIELDS + NARRATIVE_SOURCE_FIELDS
STRUCTURED_WEIGHT = 1.0
NARRATIVE_WEIGHT = 0.4
# Weighted evidence needed for a dimension to saturate at 1.0. Two or three reviewed taxonomy
# terms is strong evidence; a single passing mention in prose is not.
SATURATION = 2.5
GENERATION_METHOD = "public_catalogue_keyword_v2"
APPROVAL_CONFIDENCE_THRESHOLD = 0.70

_LEXICON = {
    "warm": "warm vanilla amber resin spice autumn winter".split(),
    "fresh": "fresh crisp clean bright spring citrus green aquatic".split(),
    "sweet": "sweet vanilla honey caramel sugar tonka".split(),
    "dark": "dark night oud incense smoke leather".split(),
    "woody": "wood woody cedar sandalwood vetiver patchouli forest grove".split(),
    "floral": "floral flower rose jasmine iris violet tuberose".split(),
    "spicy": "spicy spice pepper cinnamon cardamom clove saffron".split(),
    "fruity": "fruit fruity berry apple peach plum pear".split(),
    "green": "green leaf leafy grass moss herbal forest grove".split(),
    "aquatic": "aquatic water watery rain ocean sea".split(),
    "marine": "marine ocean sea salt coastal".split(),
    "leather": "leather suede hide".split(),
    "powdery": "powder powdery iris violet cosmetic".split(),
    "resinous": "resin resinous frankincense myrrh benzoin labdanum".split(),
    "smoky": "smoke smoky incense charred".split(),
    "gourmand": "gourmand chocolate coffee caramel pastry vanilla".split(),
    "citrus": "citrus lemon lime orange bergamot grapefruit".split(),
    "aromatic": "aromatic lavender herb herbal rosemary sage".split(),
    "amber": "amber ambery labdanum benzoin".split(),
    "musky": "musk musky skin".split(),
    "luxury": "luxury luxurious opulent refined elegant".split(),
    "projection": "projection radiant powerful bold intense".split(),
    "longevity": "longevity lasting persistent enduring intense".split(),
}


# Suffixes stripped so reviewed vocabulary unifies across its inflected forms ("woods",
# "woody" -> "wood"). Matching stays exact after stemming: a shared-prefix rule would let
# the "season" column collide with the "sea" marine keyword on every record.
_SUFFIXES = ("iness", "ness", "ing", "ies", "es", "ed", "s", "y")
_MIN_STEM = 4


def _stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= _MIN_STEM:
            return word[: -len(suffix)]
    return word


_LEXICON_STEMS = {
    dimension: {_stem(word) for word in words} for dimension, words in _LEXICON.items()
}


@dataclass(frozen=True)
class ScentVector:
    id: int
    fragrance_id: int
    values: dict[str, float]
    confidence_score: float
    generation_method: str
    review_status: str
    provenance_references: tuple[int, ...]
    source_fingerprint: str
    rejection_reason: str | None = None
    restricted_content_detected: bool = False
    private_fields_detected: bool = False


def _mapping(record: object) -> Mapping[str, object]:
    if isinstance(record, Mapping):
        return record
    if is_dataclass(record):
        return asdict(record)
    return vars(record)


def _truthy(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes", "approved"}


def _restricted(data: Mapping[str, object]) -> bool:
    if _truthy(data.get("copied_restricted_content", False)):
        return True
    # A catalogue's original description is explicitly allowed; generic/third-party content is not.
    return any(
        key in data and data[key] not in (None, "", (), [], {})
        for key in RESTRICTED_CONTENT_FIELDS - {"description"}
    )


def validate_catalogue_source(record: object) -> Mapping[str, object]:
    """Reject anything that is not an approved, public-safe catalogue projection."""
    data = _mapping(record)
    record_type = str(data.get("record_type", "catalogue_fragrance"))
    if record_type != "catalogue_fragrance":
        raise ValueError("Only catalogue fragrances can receive scent vectors")
    implicit_promoted_record = type(record).__name__ == "CatalogueFragrance"
    approved = data.get("approved", data.get("public_approved", implicit_promoted_record))
    if not _truthy(approved):
        raise ValueError("Only approved catalogue fragrances can receive scent vectors")
    if _present_supplier_private_fields(data):
        raise ValueError("Supplier-private fields cannot be used for scent vectors")
    if _restricted(data):
        raise ValueError("Restricted copied content cannot be used for scent vectors")
    try:
        if int(data["id"]) <= 0:
            raise ValueError
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("A valid catalogue fragrance ID is required") from error
    if not data.get("provenance_references"):
        raise ValueError("Catalogue provenance references are required")
    return data


def _source_payload(data: Mapping[str, object]) -> dict[str, str]:
    return {field: str(data.get(field) or "").strip().lower() for field in PUBLIC_SOURCE_FIELDS}


def _fingerprint(data: Mapping[str, object]) -> str:
    encoded = json.dumps(_source_payload(data), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _tokens(data: Mapping[str, object]) -> set[str]:
    return {
        _stem(token) for token in re.findall(r"[a-z]+", " ".join(_source_payload(data).values()))
    }


def _weighted_fields(data: Mapping[str, object]) -> list[tuple[set[str], float]]:
    """Return stemmed vocabulary per source field alongside its evidential weight."""
    payload = _source_payload(data)
    return [
        ({_stem(token) for token in re.findall(r"[a-z]+", payload[field])}, weight)
        for fields, weight in (
            (STRUCTURED_SOURCE_FIELDS, STRUCTURED_WEIGHT),
            (NARRATIVE_SOURCE_FIELDS, NARRATIVE_WEIGHT),
        )
        for field in fields
    ]


def generate_scent_vector(
    record: object, existing: Sequence[ScentVector] = ()
) -> ScentVector:
    """Generate an idempotent vector from allowlisted catalogue fields only."""
    data = validate_catalogue_source(record)
    fragrance_id = int(data["id"])
    fingerprint = _fingerprint(data)
    prior = next((item for item in existing if item.fragrance_id == fragrance_id), None)
    if prior and prior.source_fingerprint == fingerprint:
        return prior

    tokens = _tokens(data)
    weighted = _weighted_fields(data)
    values = {
        dimension: round(
            min(1.0, sum(weight * len(field_stems & stems) for field_stems, weight in weighted)
                / SATURATION),
            3,
        )
        for dimension, stems in _LEXICON_STEMS.items()
    }
    populated = sum(bool(data.get(field)) for field in PUBLIC_SOURCE_FIELDS)
    confidence = round(min(1.0, 0.35 + populated * 0.07 + min(len(tokens), 30) / 100), 3)
    references = tuple(
        int(value) for value in re.findall(r"\d+", str(data["provenance_references"]))
    ) if isinstance(data["provenance_references"], str) else tuple(
        int(value) for value in data["provenance_references"]  # type: ignore[union-attr]
    )
    explicitly_safe = _truthy(data.get("all_source_fields_public_safe", False))
    return ScentVector(
        id=prior.id if prior else max((item.id for item in existing), default=0) + 1,
        fragrance_id=fragrance_id,
        values=values,
        confidence_score=confidence,
        generation_method=GENERATION_METHOD,
        review_status="approved" if explicitly_safe and confidence >= APPROVAL_CONFIDENCE_THRESHOLD
        else "needs_human_review",
        provenance_references=references,
        source_fingerprint=fingerprint,
    )


def approve_scent_vector(vector: ScentVector) -> ScentVector:
    if vector.confidence_score < APPROVAL_CONFIDENCE_THRESHOLD:
        raise ValueError("Vector confidence is too low for approval")
    if vector.private_fields_detected:
        raise ValueError("Supplier-private fields prevent vector approval")
    if vector.restricted_content_detected:
        raise ValueError("Restricted copied content prevents vector approval")
    return replace(vector, review_status="approved", rejection_reason=None)


def reject_scent_vector(vector: ScentVector, reason: str) -> ScentVector:
    if not reason.strip():
        raise ValueError("A rejection reason is required")
    return replace(vector, review_status="rejected", rejection_reason=reason.strip())


def similarity(left: ScentVector, right: ScentVector) -> float:
    allowed = {"approved", "needs_human_review"}
    if left.review_status not in allowed or right.review_status not in allowed:
        raise ValueError("Similarity requires approved or review-safe vectors")
    a = [left.values[name] for name in VECTOR_DIMENSIONS]
    b = [right.values[name] for name in VECTOR_DIMENSIONS]
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
    return round(sum(x * y for x, y in zip(a, b, strict=True)) / norm, 6) if norm else 0.0


def public_vector(vector: ScentVector) -> dict[str, object]:
    """Return the explicit public API/CSV allowlist."""
    return {field.name: getattr(vector, field.name) for field in fields(vector)}
