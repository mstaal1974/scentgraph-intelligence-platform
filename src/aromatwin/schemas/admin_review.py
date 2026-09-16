"""Public-safe contracts for the internal human review console."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdminReviewQueueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    stage: str
    source_record_id: str
    title: str
    status: str
    confidence_score: float = Field(ge=0, le=1)
    source_confidence: float = Field(ge=0, le=1)
    licensing_risk: str
    copied_restricted_content_detected: bool
    provenance_summary: str
    blocking_reason: str | None = None
    reviewer: str | None = None
    updated_at: datetime | None = None
    next_action: str


class AdminReviewStageSummary(BaseModel):
    stage: str
    total: int = Field(ge=0)
    by_status: dict[str, int]
    blocked: int = Field(ge=0)
    requiring_human_review: int = Field(ge=0)
    ready_for_approval: int = Field(ge=0)


class AdminReviewSummary(BaseModel):
    total: int = Field(ge=0)
    by_status: dict[str, int]
    stages: list[AdminReviewStageSummary]
    blocked: int = Field(ge=0)
    requiring_human_review: int = Field(ge=0)
    ready_for_approval: int = Field(ge=0)


class AdminReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer: str = Field(min_length=1)
    reason: str | None = None


class AdminReviewDecisionResult(BaseModel):
    accepted: bool
    stage: str
    record_id: str
    status: str
    reason: str
    reviewer: str


class AdminBlockedItem(BaseModel):
    id: str
    stage: str
    source_record_id: str
    title: str
    status: str
    blocking_reason: str
    next_action: str


class AdminReadinessReport(BaseModel):
    ready: list[AdminReviewQueueItem]
    not_ready: list[AdminBlockedItem]
    ready_count: int = Field(ge=0)
    not_ready_count: int = Field(ge=0)
    maison_api_ready_count: int = Field(ge=0)


class AdminExportRow(BaseModel):
    stage: str
    record_id: str
    title: str
    status: str
    confidence: float = Field(ge=0, le=1)
    provenance_summary: str
    blocking_reason: str
    next_action: str
