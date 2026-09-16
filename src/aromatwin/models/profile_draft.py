from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from aromatwin.database import Base
from aromatwin.models.match_candidate import MatchCandidate
from aromatwin.models.supplier_item import SupplierItem


class ProfileDraft(Base):
    __tablename__ = "profile_drafts"
    __table_args__ = (
        CheckConstraint("confidence_score BETWEEN 0 AND 1", name="profile_drafts_confidence_range"),
        CheckConstraint(
            "source_confidence BETWEEN 0 AND 1", name="profile_drafts_source_confidence_range"
        ),
        CheckConstraint(
            "review_status IN ('needs_human_review','approved_for_catalogue','rejected_low_confidence','rejected_licensing_risk','rejected_duplicate','requires_more_sources')",
            name="profile_drafts_review_status",
        ),
        CheckConstraint(
            "review_status <> 'approved_for_catalogue' OR (reviewer IS NOT NULL AND approved_at IS NOT NULL AND restricted_content_detected = FALSE AND source_confidence >= 0.700)",
            name="profile_drafts_approval_guard",
        ),
        CheckConstraint(
            "review_status NOT LIKE 'rejected_%' OR (reviewer IS NOT NULL AND rejected_at IS NOT NULL AND rejection_reason IS NOT NULL)",
            name="profile_drafts_rejection_guard",
        ),
        Index("profile_drafts_review_queue_idx", "review_status", "created_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_item_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_items.id", ondelete="RESTRICT"), index=True
    )
    match_candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("match_candidates.id", ondelete="SET NULL"), index=True
    )
    candidate_brand: Mapped[str]
    candidate_fragrance_name: Mapped[str]
    likely_original_brand: Mapped[str | None]
    likely_original_name: Mapped[str | None]
    profile_title: Mapped[str]
    description_original: Mapped[str] = mapped_column(Text)
    description_generation_method: Mapped[str]
    top_notes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    heart_notes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    base_notes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    accords_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    fragrance_family: Mapped[str | None]
    gender: Mapped[str | None]
    season_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    occasion_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    mood_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    scent_vector_json: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    restricted_content_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    provenance_notes: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str]
    reviewer: Mapped[str | None]
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    supplier_item: Mapped[SupplierItem] = relationship()
    match_candidate: Mapped[MatchCandidate | None] = relationship()
