"""Strict public contracts for the anonymous Scentprint quiz."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AnswerType = Literal["single_choice", "multi_choice", "scale", "ranked_choice", "free_text_disabled"]
Band = Literal["low", "moderate", "high", "unknown", "light", "balanced", "bold", "close",
               "noticeable", "short", "long", "familiar", "exploratory"]


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScentprintQuizOption(PublicModel):
    option_id: str
    label: str


class ScentprintQuizQuestionRead(PublicModel):
    question_id: str
    section: str
    question_text: str
    answer_type: AnswerType
    options: list[ScentprintQuizOption]
    scoring_dimensions: list[str]
    required: bool
    public_safe_hint: str
    privacy_note: str


class ScentprintQuizContractRead(PublicModel):
    contract_id: str
    quiz_contract_version: str
    title: str
    purpose: str
    questions: list[ScentprintQuizQuestionRead]
    privacy_status: str


class ScentprintQuizAnswer(PublicModel):
    question_id: str
    selected_option_ids: str | list[str]


class ScentprintQuizResponseCreate(PublicModel):
    scentprint_public_alias: str = Field(pattern=r"^quiz_[a-z0-9]{6,24}$")
    responses: list[ScentprintQuizAnswer]


class ScentprintPreferenceVector(PublicModel):
    scent_family_weights: dict[str, float]
    note_family_weights: dict[str, float]
    accord_weights: dict[str, float]
    mood_weights: dict[str, float]
    occasion_weights: dict[str, float]
    season_weights: dict[str, float]
    intensity_band: str
    sweetness_band: str
    freshness_band: str
    warmth_band: str
    projection_band: str
    longevity_band: str
    avoid_note_families: list[str]
    discovery_preference_band: str


class ScentprintQuizVectorRead(PublicModel):
    scentprint_quiz_id: str
    quiz_contract_version: str
    scentprint_public_alias: str
    preference_vector: ScentprintPreferenceVector
    confidence_band: Literal["low", "moderate", "high"]
    missing_response_count: int = Field(ge=0)
    skipped_question_count: int = Field(ge=0)
    privacy_status: str
    created_at: datetime


class ScentprintQuizProductMatchRead(PublicModel):
    product_id: str
    product_title: str
    product_format: str
    match_score_band: str
    match_reason: str
    shared_families: list[str]
    shared_accords: list[str]
    shared_moods: list[str]
    public_safe_explanation: str


class ScentprintQuizResultRead(PublicModel):
    scentprint_quiz_id: str
    scentprint_public_alias: str
    result_title: str
    result_summary: str
    dominant_families: list[str]
    preferred_accords: list[str]
    preferred_moods: list[str]
    preferred_occasions: list[str]
    preferred_seasons: list[str]
    avoid_note_families: list[str]
    recommended_product_matches: list[ScentprintQuizProductMatchRead]
    recommendation_explanations: list[str]
    confidence_band: str
    review_status: str
    privacy_status: str


class ScentprintQuizPublicSummary(PublicModel):
    scentprint_public_alias: str
    dominant_families: list[str]
    confidence_band: str
    privacy_status: str


class ScentprintQuizAuditReport(PublicModel):
    passed: bool
    quiz_contract_version: str
    question_count: int
    violations: list[str]
    privacy_status: str
