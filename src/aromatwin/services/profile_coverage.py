"""Coverage reporting for the supplier-derived fragrance universe."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from aromatwin.services.bulk_profile_generation import _identity, _value

COVERAGE_STATUSES = {
    "no_profile_started", "draft_created", "needs_enrichment", "enrichment_ready",
    "approved_for_catalogue", "catalogue_published", "vector_ready", "recommendation_ready",
    "blocked_low_confidence", "blocked_private_data_risk", "blocked_missing_provenance",
}


@dataclass(frozen=True)
class ProfileCoverage:
    canonical_brand: str
    canonical_fragrance_name: str
    supplier_count: int
    supplier_offer_count: int
    has_match_candidate: bool
    has_profile_draft: bool
    has_enrichment_review: bool
    has_catalogue_record: bool
    has_scent_vector: bool
    has_recommendations: bool
    profile_status: str
    source_confidence: float | None
    missing_fields: list[str]
    next_action: str


def _index(items: Iterable[object]) -> dict[tuple[str, str], object]:
    return {_identity(item)[:2]: item for item in items}


def _flag(record: object | None, *names: str) -> bool:
    return bool(record and _value(record, *names, default=False))


def build_profile_coverage(
    supplier_offers: Iterable[object], *, match_candidates: Iterable[object] = (),
    profile_drafts: Iterable[object] = (), enrichment_reviews: Iterable[object] = (),
    catalogue_records: Iterable[object] = (), scent_vectors: Iterable[object] = (),
    recommendations: Iterable[object] = (),
) -> list[ProfileCoverage]:
    groups: dict[tuple[str, str], list[object]] = {}
    for offer in supplier_offers:
        identity = _identity(offer)[:2]
        if all(identity):
            groups.setdefault(identity, []).append(offer)
    indexes = [_index(items) for items in (match_candidates, profile_drafts, enrichment_reviews,
                                            catalogue_records, scent_vectors, recommendations)]
    rows: list[ProfileCoverage] = []
    for identity, offers in groups.items():
        match, draft, enrichment, catalogue, vector, recommendation = (
            index.get(identity) for index in indexes)
        missing = list(_value(draft, "missing_profile_fields", "missing_fields", default=[])) \
            if draft else []
        confidence = float(_value(draft, "source_confidence", default=0)) if draft else None
        private_risk = _flag(draft, "private_data_risk")
        provenance = _value(draft, "provenance_notes") if draft else None
        approved = _value(draft, "review_status") in {"approved", "approved_for_catalogue"}
        if private_risk:
            status, action = "blocked_private_data_risk", "Remove private fields and repeat review."
        elif draft and not provenance:
            status, action = "blocked_missing_provenance", "Document permitted provenance."
        elif draft and confidence is not None and confidence < 0.4:
            status, action = "blocked_low_confidence", "Verify fragrance identity."
        elif recommendation:
            status, action = "recommendation_ready", "Review recommendation readiness."
        elif vector:
            status, action = "vector_ready", "Build reviewed recommendations."
        elif catalogue and _value(catalogue, "publication_status", "status") in {"published", "active"}:
            status, action = "catalogue_published", "Build scent vector from reviewed data."
        elif catalogue or approved:
            status, action = "approved_for_catalogue", "Complete controlled catalogue promotion."
        elif enrichment and _value(enrichment, "review_status", "status") in {"approved", "reviewed"}:
            status, action = "enrichment_ready", "Submit for admin review."
        elif draft and (missing or _flag(draft, "enrichment_needed")):
            status, action = "needs_enrichment", "Complete permitted-source enrichment."
        elif draft:
            status, action = "draft_created", "Submit draft for human review."
        else:
            status, action = "no_profile_started", "Generate a review-only profile draft."
        suppliers = {str(_value(item, "supplier_name", "supplier_id", default="unknown"))
                     for item in offers}
        display = offers[0]
        rows.append(ProfileCoverage(
            canonical_brand=str(_value(display, "canonical_brand", "candidate_brand",
                                       "supplier_brand_raw", "normalised_brand", "brand")),
            canonical_fragrance_name=str(_value(display, "canonical_fragrance_name",
                                                "candidate_fragrance_name", "supplier_name_raw",
                                                "normalised_name", "fragrance_name", "name")),
            supplier_count=len(suppliers), supplier_offer_count=len(offers),
            has_match_candidate=match is not None, has_profile_draft=draft is not None,
            has_enrichment_review=enrichment is not None, has_catalogue_record=catalogue is not None,
            has_scent_vector=vector is not None, has_recommendations=recommendation is not None,
            profile_status=status, source_confidence=confidence, missing_fields=missing,
            next_action=action,
        ))
    return rows


def coverage_summary(rows: Iterable[ProfileCoverage]) -> dict[str, Any]:
    items = list(rows)
    counts = {status: sum(item.profile_status == status for item in items)
              for status in sorted(COVERAGE_STATUSES)}
    return {"total_fragrance_candidates": len(items), "status_counts": counts}
