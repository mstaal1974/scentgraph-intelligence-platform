"""Deterministic recommendations derived only from the public catalogue and safe vectors."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import UTC, datetime
from typing import Mapping, Sequence

from aromatwin.services.catalogue_promotion import _present_supplier_private_fields
from aromatwin.services.scent_vector_engine import VECTOR_DIMENSIONS, ScentVector

RECOMMENDATION_TYPES = (
    "similar_fragrance",
    "same_family",
    "same_mood",
    "same_occasion",
    "same_season",
    "contrast_pick",
    "softer_alternative",
    "stronger_alternative",
    "clone_or_inspired_by_candidate",
    "discovery_pick",
)
SAFE_VECTOR_STATUSES = frozenset({"approved", "needs_human_review", "review_safe"})
APPROVAL_CONFIDENCE_THRESHOLD = 0.70
GENERATION_METHOD = "public_safe_vector_context_v1"
RESTRICTED_MARKERS = frozenset(
    {
        "third_party_description",
        "review",
        "reviews",
        "rating",
        "ratings",
        "image",
        "image_url",
        "comment",
        "comments",
        "ugc",
        "copied_restricted_content",
    }
)
PUBLIC_RECOMMENDATION_FIELDS = (
    "id",
    "source_fragrance_id",
    "recommended_fragrance_id",
    "recommendation_type",
    "score",
    "reason",
    "shared_dimensions_json",
    "difference_summary",
    "confidence_score",
    "generation_method",
    "review_status",
    "created_at",
    "updated_at",
    "rejection_reason",
)


@dataclass(frozen=True)
class Recommendation:
    id: int
    source_fragrance_id: int
    recommended_fragrance_id: int
    recommendation_type: str
    score: float
    reason: str
    shared_dimensions_json: dict[str, object]
    difference_summary: str
    confidence_score: float
    generation_method: str
    review_status: str
    created_at: datetime
    updated_at: datetime
    rejection_reason: str | None = None
    private_fields_detected: bool = False
    restricted_content_detected: bool = False


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return asdict(value)
    return vars(value)


def _truthy(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes", "approved"}


def _tokens(value: object) -> set[str]:
    if isinstance(value, (tuple, list, set)):
        return {str(item).strip().lower() for item in value if str(item).strip()}
    return {
        item.strip().lower()
        for item in str(value or "").replace("|", ",").split(",")
        if item.strip()
    }


def validate_catalogue_record(record: object) -> Mapping[str, object]:
    data = _mapping(record)
    if str(data.get("record_type", "catalogue_fragrance")) != "catalogue_fragrance":
        raise ValueError("Recommendations require approved catalogue fragrances")
    implicit = type(record).__name__ == "CatalogueFragrance"
    if not _truthy(data.get("approved", data.get("public_approved", implicit))):
        raise ValueError("Recommendations require approved catalogue fragrances")
    if _present_supplier_private_fields(data):
        raise ValueError("Supplier-private fields cannot be used for recommendations")
    if _truthy(data.get("copied_restricted_content")) or any(
        key in data and data[key] not in (None, "", (), [], {})
        for key in RESTRICTED_MARKERS - {"copied_restricted_content"}
    ):
        raise ValueError("Restricted copied content cannot be used for recommendations")
    return data


def validate_vector(vector: ScentVector) -> None:
    if vector.review_status not in SAFE_VECTOR_STATUSES:
        raise ValueError("Recommendations require an approved or review-safe scent vector")
    if vector.private_fields_detected:
        raise ValueError("Supplier-private vector input cannot be used for recommendations")
    if vector.restricted_content_detected:
        raise ValueError("Restricted copied content cannot be used for recommendations")


def _cosine(left: ScentVector, right: ScentVector) -> float:
    a = [float(left.values.get(name, 0)) for name in VECTOR_DIMENSIONS]
    b = [float(right.values.get(name, 0)) for name in VECTOR_DIMENSIONS]
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.0


def _context(record: Mapping[str, object], field: str) -> set[str]:
    return _tokens(record.get(field) or record.get(f"{field}s"))


def _shared_context(
    source: Mapping[str, object], candidate: Mapping[str, object]
) -> dict[str, list[str]]:
    return {
        field: sorted(_context(source, field) & _context(candidate, field))
        for field in ("family", "mood", "occasion", "season", "accord")
        if _context(source, field) & _context(candidate, field)
    }


def _kind(
    source: Mapping[str, object],
    candidate: Mapping[str, object],
    left: ScentVector,
    right: ScentVector,
    shared: Mapping[str, list[str]],
    similarity: float,
) -> str:
    if _truthy(candidate.get("clone_or_inspired_by_candidate")):
        return "clone_or_inspired_by_candidate"
    source_intensity = float(source.get("intensity") or left.values.get("projection", 0))
    candidate_intensity = float(candidate.get("intensity") or right.values.get("projection", 0))
    if candidate_intensity <= source_intensity - 0.2:
        return "softer_alternative"
    if candidate_intensity >= source_intensity + 0.2:
        return "stronger_alternative"
    for field in ("family", "mood", "occasion", "season"):
        if field in shared:
            return f"same_{field}"
    if similarity <= 0.25:
        return "contrast_pick"
    return "similar_fragrance" if similarity >= 0.55 else "discovery_pick"


def _score(similarity: float, shared: Mapping[str, list[str]]) -> float:
    context_fit = min(1.0, sum(len(items) for items in shared.values()) / 4)
    return round(max(0.0, min(1.0, similarity * 0.75 + context_fit * 0.25)), 6)


def _explanation(
    kind: str, shared: Mapping[str, list[str]], left: ScentVector, right: ScentVector
) -> tuple[str, dict[str, object], str]:
    dimensions = sorted(
        (
            name
            for name in VECTOR_DIMENSIONS
            if min(left.values.get(name, 0), right.values.get(name, 0)) >= 0.25
        ),
        key=lambda name: (-min(left.values.get(name, 0), right.values.get(name, 0)), name),
    )[:4]
    details = {"vector_dimensions": dimensions, **shared}
    common = dimensions + [item for values in shared.values() for item in values]
    reason = (
        f"AromaTwin selected this {kind.replace('_', ' ')} for its shared {', '.join(common[:4])}."
        if common
        else f"AromaTwin selected this {kind.replace('_', ' ')} to broaden the scent profile."
    )
    deltas = sorted(
        (
            (name, right.values.get(name, 0) - left.values.get(name, 0))
            for name in VECTOR_DIMENSIONS
        ),
        key=lambda item: (-abs(item[1]), item[0]),
    )
    meaningful = [
        f"{'more' if delta > 0 else 'less'} {name}" for name, delta in deltas if abs(delta) >= 0.1
    ]
    difference = (
        "The option is " + ", ".join(meaningful[:3]) + "."
        if meaningful
        else "The profiles are closely balanced."
    )
    return reason, details, difference


def generate_recommendations(
    source_fragrance: object,
    catalogue: Sequence[object],
    vectors: Sequence[ScentVector],
    existing: Sequence[Recommendation] = (),
    *,
    limit: int = 10,
) -> list[Recommendation]:
    """Rank safe candidates; an existing source/candidate/type tuple is returned only once."""
    source = validate_catalogue_record(source_fragrance)
    source_id = int(source["id"])
    vector_by_fragrance = {item.fragrance_id: item for item in vectors}
    left = vector_by_fragrance.get(source_id)
    if left is None:
        raise ValueError("Source fragrance requires an approved or review-safe scent vector")
    validate_vector(left)
    candidates: list[
        tuple[float, Mapping[str, object], ScentVector, str, dict[str, list[str]]]
    ] = []
    for item in catalogue:
        candidate = validate_catalogue_record(item)
        candidate_id = int(candidate["id"])
        if candidate_id == source_id:
            continue
        right = vector_by_fragrance.get(candidate_id)
        if right is None:
            continue
        validate_vector(right)
        similarity = _cosine(left, right)
        shared = _shared_context(source, candidate)
        kind = _kind(source, candidate, left, right, shared, similarity)
        candidates.append((_score(similarity, shared), candidate, right, kind, shared))
    candidates.sort(key=lambda row: (-row[0], int(row[1]["id"]), row[3]))
    now = datetime.now(UTC)
    output: list[Recommendation] = []
    keys = {
        (item.source_fragrance_id, item.recommended_fragrance_id, item.recommendation_type): item
        for item in existing
    }
    for score, candidate, right, kind, shared in candidates[:limit]:
        key = (source_id, int(candidate["id"]), kind)
        if key in keys:
            output.append(keys[key])
            continue
        reason, dimensions, difference = _explanation(kind, shared, left, right)
        confidence = round(
            min(left.confidence_score, right.confidence_score) * (0.6 + 0.4 * score), 6
        )
        fully_approved = left.review_status == right.review_status == "approved"
        output.append(
            Recommendation(
                id=max((item.id for item in (*existing, *output)), default=0) + 1,
                source_fragrance_id=source_id,
                recommended_fragrance_id=int(candidate["id"]),
                recommendation_type=kind,
                score=score,
                reason=reason,
                shared_dimensions_json=dimensions,
                difference_summary=difference,
                confidence_score=confidence,
                generation_method=GENERATION_METHOD,
                review_status="approved" if fully_approved else "needs_human_review",
                created_at=now,
                updated_at=now,
            )
        )
    return output


def contextual_recommendations(
    catalogue: Sequence[object],
    vectors: Sequence[ScentVector],
    *,
    mood: str | None = None,
    occasion: str | None = None,
    season: str | None = None,
    family: str | None = None,
    intensity: float | None = None,
    limit: int = 10,
) -> list[dict[str, object]]:
    filters = {"mood": mood, "occasion": occasion, "season": season, "family": family}
    vector_by_fragrance = {item.fragrance_id: item for item in vectors}
    results = []
    for item in catalogue:
        data = validate_catalogue_record(item)
        vector = vector_by_fragrance.get(int(data["id"]))
        if vector is None:
            continue
        validate_vector(vector)
        if any(
            value and value.lower() not in _context(data, field) for field, value in filters.items()
        ):
            continue
        candidate_intensity = float(data.get("intensity") or vector.values.get("projection", 0))
        if intensity is not None and abs(candidate_intensity - intensity) > 0.25:
            continue
        matched = [f"{field} {value}" for field, value in filters.items() if value]
        score = round(
            max(
                0.0,
                min(
                    1.0,
                    0.5
                    + len(matched) * 0.1
                    - (abs(candidate_intensity - intensity) if intensity is not None else 0),
                ),
            ),
            6,
        )
        results.append(
            {
                "fragrance_id": int(data["id"]),
                "score": score,
                "reason": "AromaTwin matched "
                + ", ".join(matched or ["the requested intensity"])
                + ".",
            }
        )
    return sorted(results, key=lambda row: (-float(row["score"]), int(row["fragrance_id"])))[:limit]


def approve_recommendation(item: Recommendation) -> Recommendation:
    if item.confidence_score < APPROVAL_CONFIDENCE_THRESHOLD:
        raise ValueError("Recommendation confidence is too low for approval")
    if item.private_fields_detected or _present_supplier_private_fields(
        item.shared_dimensions_json
    ):
        raise ValueError("Supplier-private fields prevent recommendation approval")
    if item.restricted_content_detected or any(
        key in item.shared_dimensions_json for key in RESTRICTED_MARKERS
    ):
        raise ValueError("Restricted copied content prevents recommendation approval")
    return replace(
        item, review_status="approved", updated_at=datetime.now(UTC), rejection_reason=None
    )


def reject_recommendation(item: Recommendation, reason: str) -> Recommendation:
    if not reason.strip():
        raise ValueError("A rejection reason is required")
    return replace(
        item,
        review_status="rejected",
        rejection_reason=reason.strip(),
        updated_at=datetime.now(UTC),
    )


def public_recommendation(item: Recommendation) -> dict[str, object]:
    data = asdict(item)
    return {field: data[field] for field in PUBLIC_RECOMMENDATION_FIELDS}
