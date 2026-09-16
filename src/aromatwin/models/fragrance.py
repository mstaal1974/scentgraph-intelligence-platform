from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base
from aromatwin.models.common import TimestampMixin


class Fragrance(TimestampMixin, Base):
    __tablename__ = "fragrances"
    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    enrichment_review_id: Mapped[int] = mapped_column(
        ForeignKey("enrichment_reviews.id"), unique=True
    )
    name: Mapped[str]
    slug: Mapped[str]
    concentration: Mapped[str | None]
    description: Mapped[str | None] = mapped_column(Text)
    family: Mapped[str | None]
    gender: Mapped[str | None]
    release_year: Mapped[int | None]
    perfumer: Mapped[str | None]
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    review_status: Mapped[str] = mapped_column(ForeignKey("review_statuses.code"))
