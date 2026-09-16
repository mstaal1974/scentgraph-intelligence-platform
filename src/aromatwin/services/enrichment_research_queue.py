"""Safe, offline enrichment task preparation; this module performs no web access."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from hashlib import sha256

from aromatwin.services.bulk_profile_generation import _value

SAFE_QUESTIONS = (
    "Verify the fragrance identity from permitted sources.",
    "Identify top, heart, and base notes using sources that allow commercial use or first-party permission.",
    "Write an original description in Maison Obsidian tone after source review.",
    "Confirm whether this profile is inspired-by, original, or unclear.",
    "Confirm suitable mood, occasion, and season tags.",
)


@dataclass(frozen=True)
class ResearchQueueItem:
    queue_id: str
    profile_draft_id: str | None
    canonical_brand: str
    canonical_fragrance_name: str
    priority: int
    missing_fields: list[str]
    suggested_source_types: list[str]
    research_questions: list[str]
    licensing_risk: str
    review_status: str
    next_action: str


def build_enrichment_research_queue(coverage: Iterable[object],
                                    profile_drafts: Iterable[object] = ()) -> list[ResearchQueueItem]:
    drafts = {(str(_value(item, "canonical_brand")).casefold(),
               str(_value(item, "canonical_fragrance_name")).casefold()): item
              for item in profile_drafts}
    queue = []
    eligible = {"no_profile_started", "draft_created", "needs_enrichment",
                "blocked_low_confidence", "blocked_missing_provenance"}
    for row in coverage:
        status = str(_value(row, "profile_status"))
        missing = list(_value(row, "missing_fields", default=[]))
        if status not in eligible and not missing:
            continue
        brand = str(_value(row, "canonical_brand"))
        name = str(_value(row, "canonical_fragrance_name"))
        draft = drafts.get((brand.casefold(), name.casefold()))
        offer_count = int(_value(row, "supplier_offer_count", default=1))
        commercial_potential = int(_value(row, "commercial_potential", "maison_product_candidate",
                                          default=0) or 0)
        priority = min(100, 40 + min(30, offer_count * 10) + (20 if commercial_potential else 0)
                       + (10 if status == "no_profile_started" else 0))
        digest = sha256(f"{brand.casefold()}|{name.casefold()}".encode()).hexdigest()[:16]
        queue.append(ResearchQueueItem(
            queue_id=f"erq-{digest}",
            profile_draft_id=str(_value(draft, "profile_draft_id", "id")) if draft else None,
            canonical_brand=brand, canonical_fragrance_name=name, priority=priority,
            missing_fields=missing or ["profile_identity_review"],
            suggested_source_types=["brand_first_party", "licensed_reference", "authorised_material"],
            research_questions=list(SAFE_QUESTIONS), licensing_risk="review_required",
            review_status="needs_human_review",
            next_action="Research using permitted sources, record provenance, and submit for human review.",
        ))
    return sorted(queue, key=lambda item: (-item.priority, item.canonical_brand.casefold(),
                                           item.canonical_fragrance_name.casefold()))
