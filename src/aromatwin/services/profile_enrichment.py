"""Draft-only, privacy-preserving fragrance profile enrichment.

The offline provider deliberately infers only broad families and accords from names.
An empty note list means that no note-level evidence was supplied; it is not an
invitation to invent a plausible pyramid.

The model-backed provider sends only an allow-listed identity payload, requests a strict JSON
schema, and falls back to the offline provider on any API failure. Nothing it returns is then
trusted: the response is validated against controlled vocabularies, bounded in size, stripped of
private and restricted keys, and every field is tagged in ``field_provenance`` with whether it
came from supplied evidence or from model inference. A schema guarantees shape, not that a value
is a real season, a sane list length, or original prose. Reviewers approve specific claims, not a
blob, and no enriched record can reach the catalogue without a human decision.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Mapping

if importlib.util.find_spec("openai") is not None:
    from openai import (
        APIConnectionError,
        APIError,
        AuthenticationError,
        OpenAIError,
        RateLimitError,
    )
else:  # Keep offline-only installations usable; OpenAI remains a declared production dependency.
    class OpenAIError(Exception):
        """Compatibility base used only when the optional runtime package is absent."""

    class APIError(OpenAIError):
        """Compatibility API error."""

        pass

    class APIConnectionError(APIError):
        """Compatibility connection error."""

        pass

    class AuthenticationError(APIError):
        """Compatibility authentication error."""

        pass

    class RateLimitError(APIError):
        """Compatibility rate-limit error."""

        pass

WARNING = "AI enrichment is draft-only and requires human review before catalogue use."
OPENAI_FALLBACK_SUMMARY = (
    "OpenAI enrichment was unavailable or rate-limited; offline draft generated for human review."
)

OUTPUT_FIELDS = (
    "profile_draft_id", "brand_display_name", "fragrance_display_name",
    "fragrance_family", "top_notes", "heart_notes", "base_notes", "accords",
    "mood_tags", "occasion_tags", "season_tags", "strength_band", "longevity_band",
    "projection_band", "draft_scent_description", "ai_confidence_band",
    "enrichment_sources", "provenance_notes", "fields_requiring_human_review",
    "field_provenance", "enrichment_status", "review_status",
)

AI_DRAFT_FIELDS = (
    "fragrance_family", "top_notes", "heart_notes", "base_notes", "accords",
    "mood_tags", "occasion_tags", "season_tags", "strength_band", "longevity_band",
    "projection_band", "draft_scent_description", "ai_confidence_band",
    "fields_requiring_human_review",
)
IDENTITY_FIELDS = ("brand_display_name", "fragrance_display_name")
# This is deliberately an allow-list rather than a deny-list.  New fields from a
# supplier import therefore cannot accidentally become part of an AI request.
SAFE_METADATA_FIELDS = (
    "fragrance_family", "top_notes", "heart_notes", "base_notes", "accords",
    "mood_tags", "occasion_tags", "season_tags", "strength_band",
    "longevity_band", "projection_band", "ai_confidence_band",
    "fields_requiring_human_review", "enrichment_status", "review_status",
)
MISSING_KEY_WARNING = "OpenAI API key is not configured. Using offline demo enrichment."
ALLOWED_PROVIDERS = ("offline", "openai")

# Fields a reviewer signs off on individually. Anything here that a model asserted without
# supporting evidence is surfaced as such rather than folded into an overall confidence score.
ENRICHED_FIELDS = (
    "fragrance_family", "top_notes", "heart_notes", "base_notes", "accords", "mood_tags",
    "occasion_tags", "season_tags", "strength_band", "longevity_band", "projection_band",
    "draft_scent_description",
)
EVIDENCE_PROVENANCE = "supplier_evidence"
MODEL_PROVENANCE = "model_inference"

# Controlled vocabularies. A model answer outside these is discarded, not coerced to something
# plausible, so an unexpected value becomes a review flag instead of silent bad data.
STRENGTH_BANDS = ("light", "moderate", "strong", "unknown")
LONGEVITY_BANDS = ("short", "moderate", "long", "very long", "unknown")
PROJECTION_BANDS = ("intimate", "moderate", "strong", "unknown")
CONFIDENCE_BANDS = ("low", "medium", "high")
SEASONS = ("spring", "summer", "autumn", "winter")
OCCASIONS = ("daytime", "evening", "work", "casual", "formal", "special occasion")
MAX_LIST_ITEMS = 6
MAX_TERM_LENGTH = 40
MAX_DESCRIPTION_LENGTH = 600

# Keys that must never survive from an input draft or a model response into an enriched record.
FORBIDDEN_KEYS = frozenset(
    {
        "supplier_price", "price", "price_aed", "price_usd", "aed_price", "usd_price",
        "supplier_code", "supplier_sku", "cn_code", "stock", "quantity", "commercial_terms",
        "third_party_description", "review", "reviews", "rating", "ratings", "image",
        "image_url", "comment", "comments", "ugc", "source_url", "url",
    }
)
# Prose that suggests copied marketing or retail copy rather than original draft description.
_COPY_MARKERS = re.compile(
    r"\b(shop now|buy now|available at|official website|all rights reserved|"
    r"\u00a9|™|®|out of \d+ stars|customer reviews?)\b",
    re.IGNORECASE,
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


def _clean_term(value: object) -> str:
    """Return a bounded, lowercase term with no markup or separators."""
    text = re.sub(r"\s+", " ", str(value or "")).strip().strip(".,;:").lower()
    return text[:MAX_TERM_LENGTH] if text and "<" not in text and ">" not in text else ""


def _clean_list(value: object, allowed: tuple[str, ...] | None = None) -> list[str]:
    """Coerce a model list into bounded, deduplicated, vocabulary-checked terms."""
    if isinstance(value, str):
        items = [part for part in re.split(r"[,;|]", value)]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        return []
    cleaned = []
    for item in items:
        term = _clean_term(item)
        if not term or term in cleaned:
            continue
        if allowed is not None and term not in allowed:
            continue
        cleaned.append(term)
    return cleaned[:MAX_LIST_ITEMS]


def _clean_band(value: object, allowed: tuple[str, ...]) -> str:
    term = _clean_term(value)
    return term if term in allowed else allowed[-1]


def _clean_description(value: object) -> str:
    """Return original prose, rejecting anything that reads as copied retail or marketing copy."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text or _COPY_MARKERS.search(text):
        return ""
    return text[:MAX_DESCRIPTION_LENGTH]


def _supplied_evidence(profile: Mapping[str, Any]) -> dict[str, list[str]]:
    """Return note and accord evidence the supplier record actually stated."""
    evidence: dict[str, list[str]] = {}
    for field in ("top_notes", "heart_notes", "base_notes", "accords", "fragrance_family"):
        supplied = _clean_list(profile.get(field))
        if supplied:
            evidence[field] = supplied
    return evidence


def strip_forbidden(value: Any) -> Any:
    """Recursively drop private and restricted keys from any structure."""
    if isinstance(value, Mapping):
        return {
            key: strip_forbidden(child)
            for key, child in value.items()
            if str(key).strip().lower() not in FORBIDDEN_KEYS
        }
    if isinstance(value, list):
        return [strip_forbidden(item) for item in value]
    return value


def validate_enrichment_payload(
    payload: Mapping[str, Any], profile: Mapping[str, Any]
) -> dict[str, Any]:
    """Turn an untrusted model response into a safe, review-gated enrichment record.

    Nothing is trusted: unknown keys are dropped, vocabularies are enforced, lists are bounded,
    and every enriched field is tagged with whether it rests on supplied evidence or on model
    inference. The record always comes back needing human review.
    """
    payload = strip_forbidden(payload)
    evidence = _supplied_evidence(profile)

    family = _clean_term(payload.get("fragrance_family")) or "unclassified"
    result: dict[str, Any] = {
        "profile_draft_id": str(profile.get("profile_draft_id") or "openai-draft"),
        "brand_display_name": str(profile.get("brand_display_name", "")),
        "fragrance_display_name": str(profile.get("fragrance_display_name", "")),
        "fragrance_family": family,
        "top_notes": _clean_list(payload.get("top_notes")),
        "heart_notes": _clean_list(payload.get("heart_notes")),
        "base_notes": _clean_list(payload.get("base_notes")),
        "accords": _clean_list(payload.get("accords")),
        "mood_tags": _clean_list(payload.get("mood_tags")),
        "occasion_tags": _clean_list(payload.get("occasion_tags"), OCCASIONS),
        "season_tags": _clean_list(payload.get("season_tags"), SEASONS),
        "strength_band": _clean_band(payload.get("strength_band"), STRENGTH_BANDS),
        "longevity_band": _clean_band(payload.get("longevity_band"), LONGEVITY_BANDS),
        "projection_band": _clean_band(payload.get("projection_band"), PROJECTION_BANDS),
        "draft_scent_description": _clean_description(payload.get("draft_scent_description")),
        "ai_confidence_band": _clean_band(payload.get("ai_confidence_band"), CONFIDENCE_BANDS)
        if _clean_term(payload.get("ai_confidence_band")) in CONFIDENCE_BANDS
        else "low",
    }

    # Evidence always wins over inference: a supplier-stated value is never overwritten.
    for field, supplied in evidence.items():
        result[field] = supplied[0] if field == "fragrance_family" else supplied

    provenance = {
        field: EVIDENCE_PROVENANCE if field in evidence else MODEL_PROVENANCE
        for field in ENRICHED_FIELDS
        if result.get(field) not in (None, "", [], "unclassified", "unknown")
    }
    # Every model-asserted field needs a human decision, as do fields with nothing in them.
    review = [
        field
        for field in ENRICHED_FIELDS
        if provenance.get(field, MODEL_PROVENANCE) == MODEL_PROVENANCE
    ]
    if profile.get("blocking_issues"):
        review.append("blocking_issues")

    result["enrichment_sources"] = [
        {
            "source_type": "supplier_identity",
            "summary": "Identity fields supplied for private review.",
        },
        {
            "source_type": "model_inference",
            "summary": (
                "A language model proposed scent classification from identity fields. "
                "No third-party database record, description, or review was stored."
            ),
        },
    ]
    result["provenance_notes"] = (
        f"{WARNING} Fields marked {MODEL_PROVENANCE} are unverified model proposals and carry "
        "no source evidence; approve them only against an independent check."
    )
    result["fields_requiring_human_review"] = list(dict.fromkeys(review))
    result["field_provenance"] = provenance
    result["enrichment_status"] = "enriched_pending_review"
    result["review_status"] = "needs_human_review"
    return {field: result[field] for field in OUTPUT_FIELDS}


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
        # The offline provider asserts nothing it cannot derive from supplied identity, so what
        # it does populate is keyword inference, not evidence.
        result["field_provenance"] = {
            field: MODEL_PROVENANCE
            for field in ENRICHED_FIELDS
            if result.get(field) not in (None, "", [], "unclassified", "unknown")
        }
        return {field: result[field] for field in OUTPUT_FIELDS}


class OpenAIEnrichmentProvider(ProfileEnrichmentProvider):
    """Generate original, review-required drafts from identity fields alone."""

    def __init__(
        self, api_key: str | None = None, *, client: Any = None,
        allow_fallback: bool | None = None,
    ) -> None:
        if api_key is None and "OPENAI_API_KEY" in os.environ:
            api_key = os.environ["OPENAI_API_KEY"]
        self._available = bool(api_key)
        if client is None and api_key:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self._client = client
        self._allow_fallback = ai_fallback_allowed() if allow_fallback is None else allow_fallback

    @property
    def is_available(self) -> bool:
        return self._available

    def enrich(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        if not self.is_available:
            return self._offline_fallback(profile, reason="missing API key")
        identity = sanitise_ai_identity(profile)
        try:
            response = self._client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {"role": "system", "content": (
                        "Create an original speculative scent-profile draft using only the supplied "
                        "safe identity and non-commercial scent metadata. Do not retrieve, quote, imitate, or copy any "
                        "third-party description or review. Treat every field as requiring human review."
                    )},
                    {"role": "user", "content": json.dumps(identity, ensure_ascii=True)},
                ],
                text={"format": _response_format()},
            )
        except (RateLimitError, APIError, APIConnectionError, AuthenticationError, OpenAIError):
            return self._offline_fallback(profile, reason="OpenAI API failure")
        payload = json.loads(response.output_text)
        missing = [field for field in AI_DRAFT_FIELDS if field not in payload]
        if missing:
            raise ValueError(f"OpenAI response omitted required fields: {', '.join(missing)}")
        # The JSON schema guarantees the response shape. It does not guarantee the values are
        # in-vocabulary, bounded, free of copied marketing copy, or distinguishable from
        # supplier-stated evidence, so the payload is still validated before it is trusted.
        result = validate_enrichment_payload({**identity, **payload}, profile)
        result["enrichment_sources"] = [
            {
                "source_type": "openai_original_draft",
                "summary": (
                    "Generated only from brand and fragrance identity; no third-party text used."
                ),
            }
        ]
        return result

    def _offline_fallback(self, profile: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
        """Return a safe draft without retaining or exposing provider error details."""
        if not self._allow_fallback:
            raise RuntimeError(
                f"OpenAI enrichment unavailable ({reason}) and offline fallback is disabled"
            ) from None
        result = OfflineHeuristicEnrichmentProvider().enrich(profile)
        result["enrichment_sources"].append({
            "source_type": "offline_fallback",
            "summary": OPENAI_FALLBACK_SUMMARY,
        })
        return result


def sanitise_ai_identity(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Return the complete and exclusive payload permitted to leave the application."""
    identity = {field: str(profile.get(field, "")).strip() for field in IDENTITY_FIELDS}
    missing = [field for field, value in identity.items() if not value]
    if missing:
        raise ValueError(f"Missing required profile fields: {', '.join(missing)}")
    for field in SAFE_METADATA_FIELDS:
        value = profile.get(field)
        if isinstance(value, str) and value.strip():
            identity[field] = value.strip()
        elif isinstance(value, (list, tuple)):
            # Scalars only: nested source/provenance objects never leave the app.
            identity[field] = [item for item in value if isinstance(item, (str, int, float, bool))]
    return identity


def _response_format() -> dict[str, Any]:
    string_list = {"type": "array", "items": {"type": "string"}}
    properties = {field: string_list for field in (
        "top_notes", "heart_notes", "base_notes", "accords", "mood_tags",
        "occasion_tags", "season_tags", "fields_requiring_human_review",
    )}
    properties.update({field: {"type": "string"} for field in (
        "fragrance_family", "strength_band", "longevity_band", "projection_band",
        "draft_scent_description", "ai_confidence_band",
    )})
    return {
        "type": "json_schema", "name": "scent_profile_draft", "strict": True,
        "schema": {
            "type": "object", "properties": properties,
            "required": list(AI_DRAFT_FIELDS), "additionalProperties": False,
        },
    }


def configured_provider(value: str | None = None) -> str:
    """Validate the explicit provider setting, defaulting safely to offline."""
    provider = value if value is not None else os.environ.get("AROMATWIN_AI_PROVIDER", "offline")
    provider = provider.strip().casefold()
    if provider not in ALLOWED_PROVIDERS:
        raise ValueError("AROMATWIN_AI_PROVIDER must be one of: offline, openai")
    return provider


def ai_fallback_allowed(value: str | None = None) -> bool:
    """Read the fallback switch, defaulting to the resilient and privacy-safe path."""
    configured = value if value is not None else os.environ.get(
        "AROMATWIN_AI_ALLOW_FALLBACK", "true"
    )
    normalised = configured.strip().casefold()
    if normalised not in {"true", "false"}:
        raise ValueError("AROMATWIN_AI_ALLOW_FALLBACK must be true or false")
    return normalised == "true"


def enrich_profile(profile: Mapping[str, Any], provider: ProfileEnrichmentProvider | None = None) -> dict[str, Any]:
    """Enrich a draft using the safe offline provider by default."""
    return (provider or OfflineHeuristicEnrichmentProvider()).enrich(profile)
