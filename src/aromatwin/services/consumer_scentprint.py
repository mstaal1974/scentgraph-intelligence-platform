"""Structured preference profiles and explainable, privacy-safe matching."""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from aromatwin.schemas.consumer_scent import ConsumerScentprintCreate, ConsumerScentprintUpdate


@dataclass
class ConsumerScentprint:
    scentprint_id: str
    consumer_public_alias: str
    preferred_families: list[str]
    preferred_notes: list[str]
    preferred_accords: list[str]
    disliked_notes: list[str]
    preferred_moods: list[str]
    preferred_occasions: list[str]
    preferred_seasons: list[str]
    preferred_intensity: str | None
    preferred_projection: str | None
    preferred_longevity: str | None
    sweetness_preference: float
    freshness_preference: float
    darkness_preference: float
    woody_preference: float
    floral_preference: float
    gourmand_preference: float
    smoky_preference: float
    clean_preference: float
    adventurousness_level: str
    safe_blind_buy_tolerance: str
    preferred_product_formats: list[str]
    known_likes: list[str]
    known_dislikes: list[str]
    privacy_status: str
    review_status: str
    created_at: datetime
    updated_at: datetime


def create_scentprint(answers: ConsumerScentprintCreate) -> ConsumerScentprint:
    now = datetime.now(UTC)
    return ConsumerScentprint(scentprint_id=str(uuid4()), **answers.model_dump(),
                              review_status="needs_human_review", created_at=now, updated_at=now)


def update_scentprint(
    scentprint: ConsumerScentprint, update: ConsumerScentprintUpdate
) -> ConsumerScentprint:
    values = asdict(scentprint)
    values.update(update.model_dump(exclude_unset=True))
    values["updated_at"] = datetime.now(UTC)
    return ConsumerScentprint(**values)


def update_scentprint_from_feedback(
    scentprint: ConsumerScentprint, liked_notes: list[str], disliked_notes: list[str]
) -> ConsumerScentprint:
    """Suggest only explicit note changes; never infer personal characteristics."""
    return update_scentprint(scentprint, ConsumerScentprintUpdate(
        preferred_notes=sorted(set(scentprint.preferred_notes + liked_notes)),
        disliked_notes=sorted(set(scentprint.disliked_notes + disliked_notes)),
    ))


def public_summary(scentprint: ConsumerScentprint) -> dict[str, object]:
    return {
        "consumer_public_alias": scentprint.consumer_public_alias,
        "preferred_families": scentprint.preferred_families,
        "preferred_moods": scentprint.preferred_moods,
        "preferred_occasions": scentprint.preferred_occasions,
        "preferred_seasons": scentprint.preferred_seasons,
        "preferred_product_formats": scentprint.preferred_product_formats,
        "privacy_status": "anonymised",
    }


def match_scent_profile(
    scentprint: ConsumerScentprint, target: dict[str, object]
) -> dict[str, object]:
    """Compare allowlisted structured evidence from any supported profile record."""
    categories = (
        ("families", scentprint.preferred_families),
        ("notes", scentprint.preferred_notes),
        ("accords", scentprint.preferred_accords),
        ("moods", scentprint.preferred_moods),
        ("occasions", scentprint.preferred_occasions),
        ("seasons", scentprint.preferred_seasons),
    )
    reasons: list[str] = []
    considered = 0
    hits = 0
    for field, wanted in categories:
        offered = {str(value).casefold() for value in target.get(field, []) or []}
        wanted_values = {value.casefold() for value in wanted}
        if wanted_values and offered:
            considered += 1
            overlap = wanted_values & offered
            if overlap:
                hits += 1
                reasons.append(f"Shared {field}: {', '.join(sorted(overlap))}")
    disliked = {value.casefold() for value in scentprint.disliked_notes}
    target_notes = {str(value).casefold() for value in target.get("notes", []) or []}
    conflicts = disliked & target_notes
    score = max(0.0, (hits / considered if considered else 0.0) - 0.2 * len(conflicts))
    if conflicts:
        reasons.append("Contains explicitly disliked notes")
    if not reasons:
        reasons.append("Not enough shared structured preference evidence")
    band = "excellent" if score >= .8 else "strong" if score >= .6 else "moderate" if score >= .3 else "weak"
    return {"target_id": str(target.get("id") or target.get("fragrance_id") or "unknown"),
            "target_type": str(target.get("type") or "fragrance"), "match_band": band,
            "score": round(score, 3), "reasons": reasons}
