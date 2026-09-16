from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from aromatwin.database import Base


class ProfileEnrichmentEvent(Base):
    __tablename__ = "profile_enrichment_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_draft_id: Mapped[int] = mapped_column(
        ForeignKey("profile_drafts.id", ondelete="CASCADE")
    )
    event_type: Mapped[str]
    event_summary: Mapped[str] = mapped_column(Text)
    actor: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
