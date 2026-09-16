"""Public-safe response contracts for private operational endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PersistentRunPublicSummary(ReadModel):
    run_id: str
    run_mode: str
    workflow_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    readiness_status: str
    created_at: datetime
    updated_at: datetime


class PersistentRunRead(PersistentRunPublicSummary):
    """Internal read still intentionally excludes private filesystem locations."""


class PersistentRunStageRead(ReadModel):
    run_id: str
    stage_name: str
    stage_status: str
    accepted_count: int
    skipped_count: int
    blocked_count: int
    warning_count: int
    blocker_summary: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class PersistentArtifactRead(ReadModel):
    run_id: str
    artifact_type: str
    artifact_label: str
    storage_visibility: str
    content_hash: str | None = None
    public_safe: bool
    created_at: datetime
    storage_location: str | None = None


class PersistentProfileDraftRead(ReadModel):
    profile_draft_id: str
    run_id: str
    canonical_brand: str
    canonical_fragrance_name: str
    profile_status: str
    source_confidence_band: str
    missing_fields_json: str
    enrichment_needed: bool
    review_status: str
    provenance_summary: str | None = None
    created_at: datetime
    updated_at: datetime


class PersistentReviewItemRead(ReadModel):
    review_item_id: str
    linked_entity_type: str
    linked_entity_id: str
    review_type: str
    review_status: str
    priority_band: str
    assigned_role: str | None = None
    decision: str | None = None
    decision_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class PersistentLaunchCandidateRead(ReadModel):
    launch_candidate_id: str
    fragrance_id: str | None = None
    product_id: str | None = None
    canonical_brand: str
    canonical_fragrance_name: str
    launch_priority_band: str
    launch_status: str
    margin_suitability_band: str
    supplier_availability_band: str
    seller_demand_band: str
    consumer_interest_band: str
    blocking_issues_json: str
    recommended_next_action: str | None = None
    review_status: str
    created_at: datetime
    updated_at: datetime


class PersistentSellerDemandBriefRead(ReadModel):
    demand_brief_id: str
    seller_public_label: str
    seller_segment: str
    demand_theme: str
    product_formats_json: str
    private_data_redacted: bool
    review_status: str
    created_at: datetime
    updated_at: datetime


class PersistentConsumerScentprintRead(ReadModel):
    scentprint_id: str
    consumer_public_alias: str
    preference_summary_json: str
    privacy_status: str
    private_data_redacted: bool
    review_status: str
    created_at: datetime
    updated_at: datetime


class PersistentProvenanceRecordRead(ReadModel):
    provenance_id: str
    linked_entity_type: str
    linked_entity_id: str
    source_type: str
    source_confidence_band: str
    permitted_use_status: str
    provenance_summary: str
    review_status: str
    created_at: datetime


class PersistentAuditEventRead(ReadModel):
    audit_event_id: str
    event_type: str
    actor_type: str
    linked_entity_type: str
    linked_entity_id: str
    event_summary: str
    risk_level: str
    privacy_boundary: str
    created_at: datetime


class OperationalAuditReport(ReadModel):
    run_count: int
    stage_count: int
    review_item_count: int
    launch_candidate_count: int
    blocker_count: int
    audit_event_count: int
    run_statuses: list[dict[str, Any]]
    audit_events: list[dict[str, Any]]


class PersistenceHealthRead(ReadModel):
    status: str
    database_type: str
    destructive_initialisation: bool
