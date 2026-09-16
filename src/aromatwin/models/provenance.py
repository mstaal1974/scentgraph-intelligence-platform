from decimal import Decimal

from sqlalchemy import Boolean, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base
from aromatwin.models.common import TimestampMixin


class ReviewStatus(Base):
    __tablename__ = "review_statuses"
    code: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    terminal: Mapped[bool] = mapped_column(Boolean, default=False)


class ReferenceSource(Base):
    __tablename__ = "reference_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(unique=True)
    source_type: Mapped[str]
    permitted_use: Mapped[str]
    commercial_use_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    can_copy_text: Mapped[bool] = mapped_column(Boolean, default=False)
    can_copy_images: Mapped[bool] = mapped_column(Boolean, default=False)
    can_use_for_matching: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)


class SourceProvenance(TimestampMixin, Base):
    __tablename__ = "source_provenance"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str]
    entity_id: Mapped[int]
    source_name: Mapped[str]
    source_type: Mapped[str]
    source_reference: Mapped[str | None]
    source_url: Mapped[str | None]
    licence_status: Mapped[str]
    commercial_use_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    notes: Mapped[str | None] = mapped_column(Text)
