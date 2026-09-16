"""Privacy-separated contracts for consumer scent intelligence."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Band = Literal["low", "moderate", "high", "unknown"]
MatchBand = Literal["weak", "moderate", "strong", "excellent"]
ReviewStatus = Literal["needs_human_review", "approved", "rejected"]
WardrobeStatus = Literal[
    "owns", "tried", "wants_to_try", "not_for_me", "gifted",
    "considering_full_size", "reordered",
]


class ConsumerScentprintCreate(BaseModel):
    consumer_public_alias: str = Field(pattern=r"^[A-Za-z0-9_-]{3,40}$")
    preferred_families: list[str] = Field(default_factory=list)
    preferred_notes: list[str] = Field(default_factory=list)
    preferred_accords: list[str] = Field(default_factory=list)
    disliked_notes: list[str] = Field(default_factory=list)
    preferred_moods: list[str] = Field(default_factory=list)
    preferred_occasions: list[str] = Field(default_factory=list)
    preferred_seasons: list[str] = Field(default_factory=list)
    preferred_intensity: str | None = None
    preferred_projection: str | None = None
    preferred_longevity: str | None = None
    sweetness_preference: float = Field(default=0.5, ge=0, le=1)
    freshness_preference: float = Field(default=0.5, ge=0, le=1)
    darkness_preference: float = Field(default=0.5, ge=0, le=1)
    woody_preference: float = Field(default=0.5, ge=0, le=1)
    floral_preference: float = Field(default=0.5, ge=0, le=1)
    gourmand_preference: float = Field(default=0.5, ge=0, le=1)
    smoky_preference: float = Field(default=0.5, ge=0, le=1)
    clean_preference: float = Field(default=0.5, ge=0, le=1)
    adventurousness_level: Band = "unknown"
    safe_blind_buy_tolerance: Band = "unknown"
    preferred_product_formats: list[str] = Field(default_factory=list)
    known_likes: list[str] = Field(default_factory=list)
    known_dislikes: list[str] = Field(default_factory=list)
    privacy_status: Literal["private", "anonymised"] = "private"


class ConsumerScentprintUpdate(BaseModel):
    preferred_families: list[str] | None = None
    preferred_notes: list[str] | None = None
    preferred_accords: list[str] | None = None
    disliked_notes: list[str] | None = None
    preferred_moods: list[str] | None = None
    preferred_occasions: list[str] | None = None
    preferred_seasons: list[str] | None = None
    preferred_intensity: str | None = None
    preferred_projection: str | None = None
    preferred_longevity: str | None = None
    preferred_product_formats: list[str] | None = None


class ConsumerScentprintRead(ConsumerScentprintCreate):
    scentprint_id: str
    review_status: ReviewStatus
    created_at: datetime
    updated_at: datetime


class ConsumerScentprintPrivateRead(ConsumerScentprintRead):
    """Internal record; deliberately contains no contact or sensitive-trait fields."""


class ConsumerScentprintPublicSummary(BaseModel):
    consumer_public_alias: str
    preferred_families: list[str]
    preferred_moods: list[str]
    preferred_occasions: list[str]
    preferred_seasons: list[str]
    preferred_product_formats: list[str]
    privacy_status: str


class ConsumerScentMatchResult(BaseModel):
    target_id: str
    target_type: str
    match_band: MatchBand
    score: float = Field(ge=0, le=1)
    reasons: list[str]


class ConsumerFeedbackCreate(BaseModel):
    scentprint_id: str
    fragrance_id: str | None = None
    product_id: str | None = None
    variant_id: str | None = None
    tried_format: str | None = None
    rating_band: Literal["poor", "fair", "good", "excellent", "unrated"] = "unrated"
    would_buy_full_size: bool | None = None
    would_buy_again: bool | None = None
    perceived_sweetness: Band = "unknown"
    perceived_freshness: Band = "unknown"
    perceived_darkness: Band = "unknown"
    perceived_strength: Band = "unknown"
    perceived_longevity: Band = "unknown"
    perceived_projection: Band = "unknown"
    perceived_occassions: list[str] = Field(default_factory=list)
    perceived_seasons: list[str] = Field(default_factory=list)
    perceived_moods: list[str] = Field(default_factory=list)
    liked_notes: list[str] = Field(default_factory=list)
    disliked_notes: list[str] = Field(default_factory=list)
    free_text_private_note: str | None = None
    public_safe_quote: str | None = None


class ConsumerFeedbackRead(BaseModel):
    feedback_id: str
    fragrance_id: str | None
    product_id: str | None
    variant_id: str | None
    tried_format: str | None
    rating_band: str
    would_buy_full_size: bool | None
    would_buy_again: bool | None
    perceived_sweetness: str
    perceived_freshness: str
    perceived_darkness: str
    perceived_strength: str
    perceived_longevity: str
    perceived_projection: str
    perceived_occassions: list[str]
    perceived_seasons: list[str]
    perceived_moods: list[str]
    liked_notes: list[str]
    disliked_notes: list[str]
    public_safe_quote: str | None
    review_status: ReviewStatus
    created_at: datetime


class ConsumerFeedbackPrivateRead(ConsumerFeedbackRead):
    scentprint_id: str
    free_text_private_note: str | None


class ConsumerFeedbackPublicSummary(BaseModel):
    feedback_count: int
    rating_bands: dict[str, int]
    full_size_upgrade_rate_band: str
    repeat_purchase_intent_band: str


class CommunityScentIntelligenceRead(BaseModel):
    intelligence_id: str
    fragrance_id: str | None
    product_id: str | None
    feedback_count: int
    match_count: int
    most_common_moods: list[str]
    most_common_occasions: list[str]
    most_common_seasons: list[str]
    perceived_strength_band: str
    perceived_longevity_band: str
    perceived_projection_band: str
    full_size_upgrade_rate_band: str
    repeat_purchase_intent_band: str
    scentprint_match_clusters: list[str]
    community_summary: str
    confidence_band: str
    minimum_feedback_met: bool
    review_status: ReviewStatus
    updated_at: datetime


class CommunityScentIntelligencePublicSummary(BaseModel):
    fragrance_id: str | None
    product_id: str | None
    feedback_count: int
    most_common_moods: list[str]
    most_common_occasions: list[str]
    most_common_seasons: list[str]
    perceived_strength_band: str
    perceived_longevity_band: str
    perceived_projection_band: str
    full_size_upgrade_rate_band: str
    repeat_purchase_intent_band: str
    community_summary: str
    confidence_band: str
    minimum_feedback_met: bool


class ScentWardrobeItemCreate(BaseModel):
    scentprint_id: str
    fragrance_id: str | None = None
    product_id: str | None = None
    variant_id: str | None = None
    status: WardrobeStatus
    usage_contexts: list[str] = Field(default_factory=list)
    favourite_for: list[str] = Field(default_factory=list)
    purchase_stage: str | None = None
    last_used_season: str | None = None
    reorder_interest: Band = "unknown"
    next_recommendation_action: str | None = None


class ScentWardrobeItemUpdate(BaseModel):
    status: WardrobeStatus | None = None
    usage_contexts: list[str] | None = None
    favourite_for: list[str] | None = None
    purchase_stage: str | None = None
    last_used_season: str | None = None
    reorder_interest: Band | None = None
    next_recommendation_action: str | None = None


class ScentWardrobeItemRead(ScentWardrobeItemCreate):
    wardrobe_item_id: str
    created_at: datetime
    updated_at: datetime


class ScentWardrobePrivateRead(ScentWardrobeItemRead):
    """Private-by-default wardrobe projection."""


class ConsumerScentAuditReport(BaseModel):
    passed: bool
    scentprint_count: int
    feedback_count: int
    intelligence_count: int
    wardrobe_item_count: int
    privacy_violations: list[str]
