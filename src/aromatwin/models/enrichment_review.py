from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from aromatwin.database import Base


class EnrichmentReview(Base):
    __tablename__ = "enrichment_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("match_candidates.id"), unique=True
    )
    profile_draft_id: Mapped[int | None] = mapped_column(
        ForeignKey("profile_drafts.id"), unique=True
    )
    approved_brand: Mapped[str]
    approved_fragrance_name: Mapped[str]
    official_source_url: Mapped[str | None]
    official_source_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_summary: Mapped[str | None] = mapped_column(Text)
    description_original: Mapped[str | None] = mapped_column(Text)
    description_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    description_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    note_pyramid_json: Mapped[dict[str, list[str]]] = mapped_column(JSON, default=dict)
    top_notes: Mapped[list[str]] = mapped_column(JSON, default=list)
    heart_notes: Mapped[list[str]] = mapped_column(JSON, default=list)
    base_notes: Mapped[list[str]] = mapped_column(JSON, default=list)
    accords: Mapped[list[str]] = mapped_column(JSON, default=list)
    fragrance_family: Mapped[str | None]
    gender: Mapped[str | None]
    season: Mapped[list[str]] = mapped_column(JSON, default=list)
    occasion: Mapped[list[str]] = mapped_column(JSON, default=list)
    mood: Mapped[list[str]] = mapped_column(JSON, default=list)
    scent_vector_status: Mapped[str | None]
    scent_vector_json: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    enrichment_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
    licensing_risk: Mapped[str] = mapped_column(default="high")
    copied_text_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    review_status: Mapped[str]
    reviewer: Mapped[str | None]
    review_notes: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
