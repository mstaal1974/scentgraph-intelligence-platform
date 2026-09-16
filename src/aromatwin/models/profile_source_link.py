from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from aromatwin.database import Base
from aromatwin.models.enrichment_source import EnrichmentSource


class ProfileSourceLink(Base):
    __tablename__ = "profile_source_links"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_draft_id: Mapped[int] = mapped_column(
        ForeignKey("profile_drafts.id", ondelete="CASCADE")
    )
    enrichment_source_id: Mapped[int] = mapped_column(
        ForeignKey("enrichment_sources.id", ondelete="RESTRICT")
    )
    usage_type: Mapped[str]
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source: Mapped[EnrichmentSource] = relationship()
