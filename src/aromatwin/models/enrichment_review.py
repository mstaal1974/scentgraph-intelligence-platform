from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from aromatwin.database import Base


class EnrichmentReview(Base):
    __tablename__ = "enrichment_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_candidate_id: Mapped[int] = mapped_column(ForeignKey("match_candidates.id"), unique=True)
    approved_brand: Mapped[str]
    approved_fragrance_name: Mapped[str]
    official_source_url: Mapped[str | None]
    official_source_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description_original: Mapped[str | None] = mapped_column(Text)
    description_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    description_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
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
    review_status: Mapped[str] = mapped_column(ForeignKey("review_statuses.code"))
    reviewer: Mapped[str | None]
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
