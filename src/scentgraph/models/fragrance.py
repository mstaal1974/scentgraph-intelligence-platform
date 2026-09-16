from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from scentgraph.database import Base


class Fragrance(Base):
    __tablename__ = "fragrances"
    __table_args__ = (UniqueConstraint("brand_id", "slug", "concentration"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String)
    concentration: Mapped[str | None]
    description: Mapped[str | None] = mapped_column(Text)
    family: Mapped[str | None]
    gender: Mapped[str | None]
    release_year: Mapped[int | None] = mapped_column(SmallInteger)
    perfumer: Mapped[str | None]
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    brand: Mapped["Brand"] = relationship(back_populates="fragrances")  # noqa: F821
