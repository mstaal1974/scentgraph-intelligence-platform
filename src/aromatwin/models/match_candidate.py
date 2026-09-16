from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class MatchCandidate(Base):
    __tablename__ = "match_candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_item_id: Mapped[int] = mapped_column(ForeignKey("supplier_items.id"))
    candidate_brand: Mapped[str]
    candidate_fragrance_name: Mapped[str]
    candidate_concentration: Mapped[str | None]
    candidate_source_type: Mapped[str]
    candidate_source_reference: Mapped[str | None]
    reference_source_id: Mapped[int | None] = mapped_column(ForeignKey("reference_sources.id"))
    match_method: Mapped[str]
    match_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    match_notes: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(ForeignKey("review_statuses.code"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
