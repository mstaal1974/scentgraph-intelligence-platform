from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class ProfileDraft(Base):
    __tablename__ = "profile_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_item_id: Mapped[int] = mapped_column(ForeignKey("supplier_items.id"))
    match_candidate_id: Mapped[int] = mapped_column(ForeignKey("match_candidates.id"))
    brand: Mapped[str]
    fragrance_name: Mapped[str]
    concentration: Mapped[str | None]
    description: Mapped[str] = mapped_column(Text)
    provenance_notes: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str]
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    review_status: Mapped[str] = mapped_column(ForeignKey("review_statuses.code"))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

