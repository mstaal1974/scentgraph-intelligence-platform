from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from aromatwin.database import Base


class EnrichmentSource(Base):
    __tablename__ = "enrichment_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str]
    source_type: Mapped[str]
    source_url: Mapped[str | None]
    source_title: Mapped[str | None]
    source_domain: Mapped[str | None]
    commercial_use_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    can_copy_text: Mapped[bool] = mapped_column(Boolean, default=False)
    can_copy_images: Mapped[bool] = mapped_column(Boolean, default=False)
    can_use_for_factual_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    can_use_for_matching: Mapped[bool] = mapped_column(Boolean, default=False)
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
