"""Operational SQLAlchemy models containing summaries, states, and provenance only."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class CreatedMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class UpdatedMixin(CreatedMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PersistentRun(UpdatedMixin, Base):
    __tablename__ = "persistent_runs"
    run_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    run_mode: Mapped[str] = mapped_column(String(40))
    workflow_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="created")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    readiness_status: Mapped[str] = mapped_column(String(40), default="pending")
    private_output_root: Mapped[str | None] = mapped_column(Text)
    public_summary_path: Mapped[str | None] = mapped_column(Text)


class PersistentRunStage(CreatedMixin, Base):
    __tablename__ = "persistent_run_stages"
    __table_args__ = (UniqueConstraint("run_id", "stage_name"),)
    run_id: Mapped[str] = mapped_column(String(100), index=True)
    stage_name: Mapped[str] = mapped_column(String(100))
    stage_status: Mapped[str] = mapped_column(String(40))
    accepted_count: Mapped[int] = mapped_column(default=0)
    skipped_count: Mapped[int] = mapped_column(default=0)
    blocked_count: Mapped[int] = mapped_column(default=0)
    warning_count: Mapped[int] = mapped_column(default=0)
    blocker_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PersistentArtifact(CreatedMixin, Base):
    __tablename__ = "persistent_artifacts"
    __table_args__ = (UniqueConstraint("run_id", "artifact_type", "artifact_label"),)
    run_id: Mapped[str] = mapped_column(String(100), index=True)
    artifact_type: Mapped[str] = mapped_column(String(80))
    artifact_label: Mapped[str] = mapped_column(String(160))
    storage_location: Mapped[str] = mapped_column(Text)
    storage_visibility: Mapped[str] = mapped_column(String(30), default="private")
    content_hash: Mapped[str | None] = mapped_column(String(128))
    public_safe: Mapped[bool] = mapped_column(Boolean, default=False)


class PersistentProfileDraft(UpdatedMixin, Base):
    __tablename__ = "persistent_profile_drafts"
    profile_draft_id: Mapped[str] = mapped_column(String(100), unique=True)
    run_id: Mapped[str] = mapped_column(String(100), index=True)
    canonical_brand: Mapped[str] = mapped_column(String(160))
    canonical_fragrance_name: Mapped[str] = mapped_column(String(200))
    profile_status: Mapped[str] = mapped_column(String(40))
    source_confidence_band: Mapped[str] = mapped_column(String(40))
    missing_fields_json: Mapped[str] = mapped_column(Text, default="[]")
    enrichment_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    review_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    provenance_summary: Mapped[str | None] = mapped_column(Text)


class PersistentReviewItem(UpdatedMixin, Base):
    __tablename__ = "persistent_review_items"
    review_item_id: Mapped[str] = mapped_column(String(100), unique=True)
    linked_entity_type: Mapped[str] = mapped_column(String(80), index=True)
    linked_entity_id: Mapped[str] = mapped_column(String(100), index=True)
    review_type: Mapped[str] = mapped_column(String(80))
    review_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    priority_band: Mapped[str] = mapped_column(String(40))
    assigned_role: Mapped[str | None] = mapped_column(String(80))
    decision: Mapped[str | None] = mapped_column(String(80))
    decision_reason: Mapped[str | None] = mapped_column(Text)


class PersistentLaunchCandidate(UpdatedMixin, Base):
    __tablename__ = "persistent_launch_candidates"
    launch_candidate_id: Mapped[str] = mapped_column(String(100), unique=True)
    fragrance_id: Mapped[str | None] = mapped_column(String(100))
    product_id: Mapped[str | None] = mapped_column(String(100))
    canonical_brand: Mapped[str] = mapped_column(String(160))
    canonical_fragrance_name: Mapped[str] = mapped_column(String(200))
    launch_priority_band: Mapped[str] = mapped_column(String(40))
    launch_status: Mapped[str] = mapped_column(String(40), default="candidate", index=True)
    margin_suitability_band: Mapped[str] = mapped_column(String(40))
    supplier_availability_band: Mapped[str] = mapped_column(String(40))
    seller_demand_band: Mapped[str] = mapped_column(String(40))
    consumer_interest_band: Mapped[str] = mapped_column(String(40))
    blocking_issues_json: Mapped[str] = mapped_column(Text, default="[]")
    recommended_next_action: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)


class PersistentSellerDemandBrief(UpdatedMixin, Base):
    __tablename__ = "persistent_seller_demand_briefs"
    demand_brief_id: Mapped[str] = mapped_column(String(100), unique=True)
    seller_public_label: Mapped[str] = mapped_column(String(160))
    seller_segment: Mapped[str] = mapped_column(String(80))
    demand_theme: Mapped[str] = mapped_column(String(160))
    product_formats_json: Mapped[str] = mapped_column(Text, default="[]")
    private_data_redacted: Mapped[bool] = mapped_column(Boolean, default=True)
    review_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)


class PersistentConsumerScentprint(UpdatedMixin, Base):
    __tablename__ = "persistent_consumer_scentprints"
    scentprint_id: Mapped[str] = mapped_column(String(100), unique=True)
    consumer_public_alias: Mapped[str] = mapped_column(String(160))
    preference_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    privacy_status: Mapped[str] = mapped_column(String(40), default="redacted")
    private_data_redacted: Mapped[bool] = mapped_column(Boolean, default=True)
    review_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)


class PersistentProvenanceRecord(CreatedMixin, Base):
    __tablename__ = "persistent_provenance_records"
    provenance_id: Mapped[str] = mapped_column(String(100), unique=True)
    linked_entity_type: Mapped[str] = mapped_column(String(80), index=True)
    linked_entity_id: Mapped[str] = mapped_column(String(100), index=True)
    source_type: Mapped[str] = mapped_column(String(80))
    source_confidence_band: Mapped[str] = mapped_column(String(40))
    permitted_use_status: Mapped[str] = mapped_column(String(40))
    provenance_summary: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(40), default="pending", index=True)


class PersistentAuditEvent(CreatedMixin, Base):
    __tablename__ = "persistent_audit_events"
    audit_event_id: Mapped[str] = mapped_column(String(100), unique=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    actor_type: Mapped[str] = mapped_column(String(40))
    linked_entity_type: Mapped[str] = mapped_column(String(80), index=True)
    linked_entity_id: Mapped[str] = mapped_column(String(100), index=True)
    event_summary: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(30))
    privacy_boundary: Mapped[str] = mapped_column(String(40))
