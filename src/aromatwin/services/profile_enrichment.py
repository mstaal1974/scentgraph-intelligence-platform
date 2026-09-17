"""Draft-only, privacy-preserving fragrance profile enrichment.

The offline provider deliberately infers only broad families and accords from names.
An empty note list means that no note-level evidence was supplied; it is not an
invitation to invent a plausible pyramid.

The model-backed provider may propose a note pyramid, but nothing it returns is trusted:
output is validated against controlled vocabularies, bounded in size, stripped of private
and restricted keys, and every field is tagged in ``field_provenance`` with whether it came
from supplied evidence or from model inference. Reviewers approve specific claims, not a blob.
No enriched record can reach the catalogue without a human decision.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Mapping

WARNING = "AI enrichment is draft-only and requires human review before catalogue use."

OUTPUT_FIELDS = (
    "profile_draft_id", "brand_display_name", "fragrance_display_name",
    "fragrance_family", "top_notes", "heart_notes", "base_notes", "accords",
    "mood_tags", "occasion_tags", "season_tags", "strength_band", "longevity_band",
    "projection_band", "draft_scent_description", "ai_confidence_band",
    "enrichment_sources", "provenance_notes", "fields_requiring_human_review",
    "field_provenance", "enrichment_status", "review_status",
)

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
        "profile_draft_id": str(profile["profile_draft_id"]),
        "brand_display_name": str(profile["brand_display_name"]),
        "fragrance_display_name": str(profile["fragrance_display_name"]),
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


DEFAULT_MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You classify fragrances for a commercial fragrance-intelligence platform. "
    "Return JSON only, matching the requested keys exactly.\n"
    "Rules you must follow:\n"
    "1. Write the description in your own words. Never reproduce marketing copy, retailer "
    "text, a third-party database entry, a review, or any quoted material.\n"
    "2. Do not include URLs, ratings, review text, prices, or supplier identifiers.\n"
    "3. Report genuine uncertainty. Set ai_confidence_band to \"low\" when you are inferring "
    "from a name alone, and leave a list empty rather than guessing to fill it.\n"
    "4. Use only these vocabularies. season_tags: "
    + ", ".join(SEASONS)
    + ". occasion_tags: "
    + ", ".join(OCCASIONS)
    + ". strength_band: "
    + ", ".join(STRENGTH_BANDS)
    + ". longevity_band: "
    + ", ".join(LONGEVITY_BANDS)
    + ". projection_band: "
    + ", ".join(PROJECTION_BANDS)
    + "."
)
REQUESTED_KEYS = (
    "fragrance_family", "top_notes", "heart_notes", "base_notes", "accords", "mood_tags",
    "occasion_tags", "season_tags", "strength_band", "longevity_band", "projection_band",
    "draft_scent_description", "ai_confidence_band",
)


def build_user_prompt(profile: Mapping[str, Any]) -> str:
    """Describe one draft to the model using identity and stated evidence only."""
    evidence = _supplied_evidence(profile)
    lines = [
        f"Brand: {profile['brand_display_name']}",
        f"Fragrance: {profile['fragrance_display_name']}",
    ]
    concentration = _clean_term(profile.get("concentration"))
    if concentration:
        lines.append(f"Concentration: {concentration}")
    if evidence:
        lines.append("Evidence stated by the supplier record (treat as authoritative):")
        lines.extend(
            f"  {field}: {', '.join(values) if isinstance(values, list) else values}"
            for field, values in evidence.items()
        )
    else:
        lines.append("No scent evidence was supplied. Infer only what the identity supports.")
    lines.append("Return JSON with exactly these keys: " + ", ".join(REQUESTED_KEYS) + ".")
    return "\n".join(lines)


class OpenAIEnrichmentProvider(ProfileEnrichmentProvider):
    """Model-backed enrichment whose every output is validated and review-gated.

    The model proposes; it never decides. Responses pass through
    ``validate_enrichment_payload``, so an unparseable, out-of-vocabulary, oversized, or
    private-field-carrying answer degrades into a flagged draft instead of bad catalogue data.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = DEFAULT_MODEL,
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = client

    @property
    def is_available(self) -> bool:
        return bool(self._client or self.api_key)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ModuleNotFoundError as error:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "OpenAI enrichment needs the optional dependency: pip install -e '.[ai]'"
            ) from error
        self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _complete(self, profile: Mapping[str, Any]) -> str:
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(profile)},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    def enrich(self, profile: Mapping[str, Any]) -> dict[str, Any]:
        if not self.is_available:
            raise RuntimeError("OpenAI enrichment skipped: OPENAI_API_KEY is not configured")
        required = ("profile_draft_id", "brand_display_name", "fragrance_display_name")
        missing = [field for field in required if not str(profile.get(field, "")).strip()]
        if missing:
            raise ValueError(f"Missing required profile fields: {', '.join(missing)}")
        try:
            payload = json.loads(self._complete(profile))
        except (json.JSONDecodeError, KeyError, IndexError, AttributeError, TypeError):
            # A malformed answer must not lose the record: fall back to the deterministic
            # provider so the draft still reaches review, marked for full human attention.
            fallback = OfflineHeuristicEnrichmentProvider().enrich(profile)
            fallback["provenance_notes"] = (
                f"{WARNING} The model response could not be parsed; this record was built by "
                "the deterministic offline provider and needs full human enrichment."
            )
            fallback["ai_confidence_band"] = "low"
            return fallback
        if not isinstance(payload, Mapping):
            payload = {}
        return validate_enrichment_payload(payload, profile)


def enrich_profile(profile: Mapping[str, Any], provider: ProfileEnrichmentProvider | None = None) -> dict[str, Any]:
    """Enrich a draft using the safe offline provider by default."""
    return (provider or OfflineHeuristicEnrichmentProvider()).enrich(profile)

