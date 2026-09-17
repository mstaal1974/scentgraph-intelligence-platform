"""Draft-only, privacy-preserving fragrance profile enrichment.

The offline provider deliberately infers only broad families and accords from names.
An empty note list means that no note-level evidence was supplied; it is not an
invitation to invent a plausible pyramid.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Mapping

WARNING = "AI enrichment is draft-only and requires human review before catalogue use."

OUTPUT_FIELDS = (
    "profile_draft_id", "brand_display_name", "fragrance_display_name",
    "fragrance_family", "top_notes", "heart_notes", "base_notes", "accords",
    "mood_tags", "occasion_tags", "season_tags", "strength_band", "longevity_band",
    "projection_band", "draft_scent_description", "ai_confidence_band",
    "enrichment_sources", "provenance_notes", "fields_requiring_human_review",
    "enrichment_status", "review_status",
)

# Keywords are evidence for broad classification only, never for an exact note pyramid.
_FAMILY_RULES: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...] = (
    (("oud", "amber", "oriental"), "amber woody", ("amber", "woody"), ("opulent", "warm"), ("evening", "special occasion")),
    (("rose", "jasmine", "floral", "bouquet"), "floral", ("floral",), ("romantic", "elegant"), ("daytime", "special occasion")),
    (("citrus", "lemon", "bergamot", "orange"), "citrus", ("citrus", "fresh"), ("bright", "uplifting"), ("daytime", "casual")),
    (("ocean", "aqua", "marine", "sea"), "fresh aquatic", ("aquatic", "fresh"), ("clean", "energising"), ("daytime", "casual")),
    (("wood", "cedar", "sandal"), "woody", ("woody",), ("grounded", "calm"), ("daytime", "evening")),
    (("vanilla", "sweet", "caramel", "gourmand"), "gourmand", ("sweet", "gourmand"), ("comforting", "playful"), ("evening", "casual")),
    (("spice", "pepper", "saffron"), "spicy", ("spicy",), ("bold", "warm"), ("evening",)),
)


class ProfileEnrichmentProvider(ABC):
    """Provider contract for enriching one minimal private profile draft."""

    @property
    def is_available(self) -> bool:
        return True

    @abstractmethod
    def enrich(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        """Return the safe enriched projection of ``profile``."""


class OfflineHeuristicEnrichmentProvider(ProfileEnrichmentProvider):
    """Deterministic enrichment requiring neither network access nor secrets."""

    def enrich(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        required = ("profile_draft_id", "brand_display_name", "fragrance_display_name")
        missing = [field for field in required if not str(profile.get(field, "")).strip()]
        if missing:
            raise ValueError(f"Missing required profile fields: {', '.join(missing)}")

        name = f"{profile['brand_display_name']} {profile['fragrance_display_name']}".casefold()
        match = next((rule for rule in _FAMILY_RULES if any(word in name for word in rule[0])), None)
        if match:
            _, family, accords, moods, occasions = match
            seasons = ["autumn", "winter"] if family in {"amber woody", "gourmand", "spicy"} else ["spring", "summer"]
            description = (
                f"A draft {family} direction for {profile['fragrance_display_name']}, "
                f"with a {', '.join(accords)} character suggested by its name."
            )
            confidence = "medium" if str(profile.get("confidence_band", "")).casefold() == "high" else "low"
            sources = [{"source_type": "supplier_identity", "summary": "Identity fields supplied for private review."},
                       {"source_type": "offline_taxonomy", "summary": "Broad family and accord keywords matched deterministically."}]
        else:
            family, accords, moods, occasions, seasons = "unclassified", [], [], [], []
            description = (
                f"A scent direction for {profile['fragrance_display_name']} has not yet been "
                "established from the available identity evidence."
            )
            confidence = "low"
            sources = [{"source_type": "supplier_identity", "summary": "Identity fields only; no scent evidence was available."}]

        review_fields = ["top_notes", "heart_notes", "base_notes", "strength_band",
                         "longevity_band", "projection_band"]
        if not match:
            review_fields += ["fragrance_family", "accords", "mood_tags", "occasion_tags", "season_tags"]
        if profile.get("blocking_issues"):
            review_fields.append("blocking_issues")
        result = {
            "profile_draft_id": str(profile["profile_draft_id"]),
            "brand_display_name": str(profile["brand_display_name"]),
            "fragrance_display_name": str(profile["fragrance_display_name"]),
            "fragrance_family": family, "top_notes": [], "heart_notes": [], "base_notes": [],
            "accords": list(accords), "mood_tags": list(moods), "occasion_tags": list(occasions),
            "season_tags": list(seasons), "strength_band": "unknown",
            "longevity_band": "unknown", "projection_band": "unknown",
            "draft_scent_description": description, "ai_confidence_band": confidence,
            "enrichment_sources": sources,
            "provenance_notes": f"{WARNING} No exact notes are asserted without evidence.",
            "fields_requiring_human_review": list(dict.fromkeys(review_fields)),
            "enrichment_status": "enriched_pending_review",
            "review_status": "needs_human_review",
        }
        return {field: result[field] for field in OUTPUT_FIELDS}


class OpenAIEnrichmentProvider(ProfileEnrichmentProvider):
    """Reserved provider boundary; live generation is intentionally not implemented yet."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def enrich(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        if not self.is_available:
            raise RuntimeError("OpenAI enrichment skipped: OPENAI_API_KEY is not configured")
        raise NotImplementedError(
            "OpenAI enrichment is a placeholder. Any implementation must generate original text, "
            "store source summaries only, and retain mandatory human review."
        )


def enrich_profile(profile: Mapping[str, Any], provider: ProfileEnrichmentProvider | None = None) -> dict[str, Any]:
    """Enrich a draft using the safe offline provider by default."""
    return (provider or OfflineHeuristicEnrichmentProvider()).enrich(profile)

