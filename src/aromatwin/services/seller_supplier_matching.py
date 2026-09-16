"""Explainable demand-to-offer matching with safe-by-default projections."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

from aromatwin.services.seller_demand_briefs import SellerDemandBrief


@dataclass
class SellerSupplierMatch:
    match_id: str
    demand_brief_id: str
    supplier_offer_id: str
    catalogue_fragrance_id: int | None
    match_candidate_id: int | None
    canonical_brand: str | None
    canonical_fragrance_name: str
    supplier_name_public_label: str
    scent_fit_score: float
    commercial_fit_score: float
    launch_readiness_score: float
    overall_match_score: float
    margin_suitability_band: str
    match_reasons: list[str]
    missing_requirements: list[str]
    risk_flags: list[str]
    next_action: str
    review_status: str
    created_at: datetime
    updated_at: datetime
    # Aggregation inputs stay internal and are removed from public-safe output.
    supplier_internal_key: str
    product_formats_internal: list[str]
    fragrance_families_internal: list[str]
    moods_internal: list[str]
    occasions_internal: list[str]
    seasons_internal: list[str]


def _get(candidate: object, key: str, default: Any = None) -> Any:
    return candidate.get(key, default) if isinstance(candidate, dict) else getattr(candidate, key, default)


def _terms(values: object) -> set[str]:
    if not values:
        return set()
    if isinstance(values, str):
        values = values.split("|")
    return {str(value).strip().casefold() for value in values if str(value).strip()}


def _overlap(wanted: list[str], offered: object) -> tuple[float, set[str]]:
    target, available = _terms(wanted), _terms(offered)
    common = target & available
    return (len(common) / len(target) if target else 0.5), common


def _public_label(name: str) -> str:
    digest = sha256(name.casefold().encode()).hexdigest()[:8].upper()
    return f"Supplier {digest}"


def match_brief_to_candidates(
    brief: SellerDemandBrief, candidates: list[object]
) -> list[SellerSupplierMatch]:
    """Rank existing offers/candidates; this function never creates catalogue records or SKUs."""
    now = datetime.now(UTC)
    matches: list[SellerSupplierMatch] = []
    for candidate in candidates:
        family, family_hits = _overlap(brief.desired_fragrance_families, _get(candidate, "fragrance_families", []))
        note, note_hits = _overlap(brief.desired_notes, _get(candidate, "notes", []))
        accord, accord_hits = _overlap(brief.desired_accords, _get(candidate, "accords", []))
        mood, mood_hits = _overlap(brief.desired_moods, _get(candidate, "moods", []))
        occasion, occasion_hits = _overlap(brief.desired_occasions, _get(candidate, "occasions", []))
        season, season_hits = _overlap(brief.desired_seasons, _get(candidate, "seasons", []))
        formats = _terms(_get(candidate, "product_formats", []))
        format_fit = len(_terms(brief.product_formats) & formats) / len(brief.product_formats)
        profile = float(_get(candidate, "profile_completeness", _get(candidate, "confidence_score", 0.0)) or 0)
        catalogue = 1.0 if _get(candidate, "linked_catalogue_fragrance_id") is not None else float(_get(candidate, "catalogue_readiness", 0.0) or 0)
        availability = 1.0 if str(_get(candidate, "offer_status", "active")).casefold() in {"active", "available", "in_stock"} else 0.2
        source = float(_get(candidate, "source_confidence", _get(candidate, "confidence_score", 0.0)) or 0)
        missing_reference = not (_get(candidate, "supplier_reference_raw") or _get(candidate, "normalised_reference") or _get(candidate, "reference"))
        if missing_reference:
            source *= 0.65
        scent = (family * 0.25 + note * 0.25 + accord * 0.2 + mood * 0.1 + occasion * 0.1 + season * 0.1)
        margin_band = str(_get(candidate, "margin_suitability_band", "unknown")).casefold()
        margin_value = {"strong": 1.0, "moderate": 0.7, "low": 0.35, "unknown": 0.45}.get(margin_band, 0.45)
        commercial = availability * 0.35 + format_fit * 0.35 + margin_value * 0.3
        readiness = profile * 0.4 + catalogue * 0.3 + source * 0.2 + format_fit * 0.1
        risks, missing = [], []
        if missing_reference:
            risks.append("missing_reference")
        if profile < 0.7:
            missing.append("profile_enrichment")
        if not formats:
            missing.append("format_suitability")
        if catalogue < 0.7:
            missing.append("catalogue_review")
        if availability < 1:
            risks.append("availability_unconfirmed")
        reasons = []
        for label, hits in (("family", family_hits), ("note", note_hits), ("accord", accord_hits), ("mood", mood_hits), ("occasion", occasion_hits), ("season", season_hits)):
            if hits:
                reasons.append(f"{label} fit: {', '.join(sorted(hits))}")
        if format_fit:
            reasons.append("requested product format is supported")
        overall = scent * 0.45 + commercial * 0.25 + readiness * 0.3
        supplier = str(_get(candidate, "supplier_name", "private-supplier"))
        offer_id = str(_get(candidate, "supplier_offer_id", f"offer:{uuid4()}"))
        matches.append(SellerSupplierMatch(
            match_id=str(uuid4()), demand_brief_id=brief.demand_brief_id,
            supplier_offer_id=offer_id,
            catalogue_fragrance_id=_get(candidate, "linked_catalogue_fragrance_id"),
            match_candidate_id=_get(candidate, "linked_match_candidate_id"),
            canonical_brand=_get(candidate, "candidate_brand", _get(candidate, "canonical_brand")),
            canonical_fragrance_name=str(_get(candidate, "candidate_fragrance_name", _get(candidate, "canonical_fragrance_name", _get(candidate, "supplier_name_raw", "Unresolved candidate")))),
            supplier_name_public_label=_public_label(supplier), scent_fit_score=round(scent, 3),
            commercial_fit_score=round(commercial, 3), launch_readiness_score=round(readiness, 3),
            overall_match_score=round(overall, 3), margin_suitability_band=margin_band,
            match_reasons=reasons, missing_requirements=missing, risk_flags=risks,
            next_action="human launch review" if not missing else "complete profiling and enrichment",
            review_status="needs_human_review", created_at=now, updated_at=now,
            supplier_internal_key=supplier, product_formats_internal=sorted(formats),
            fragrance_families_internal=list(brief.desired_fragrance_families),
            moods_internal=list(brief.desired_moods), occasions_internal=list(brief.desired_occasions),
            seasons_internal=list(brief.desired_seasons)))
    return sorted(matches, key=lambda item: item.overall_match_score, reverse=True)


def public_safe_match(match: SellerSupplierMatch) -> dict[str, object]:
    result = asdict(match)
    for key in ("supplier_offer_id", "supplier_internal_key", "product_formats_internal", "fragrance_families_internal", "moods_internal", "occasions_internal", "seasons_internal"):
        result.pop(key)
    return result
