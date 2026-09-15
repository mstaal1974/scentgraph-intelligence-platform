from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from scentgraph.database import Base

VECTOR_DIMENSIONS = (
    "warm",
    "fresh",
    "sweet",
    "dark",
    "woody",
    "floral",
    "spicy",
    "fruit",
    "green",
    "aquatic",
    "marine",
    "leather",
    "powdery",
    "resinous",
    "smoky",
    "gourmand",
    "citrus",
    "aromatic",
    "luxury",
    "projection",
    "longevity",
)


class ScentVector(Base):
    __tablename__ = "scent_vectors"
    fragrance_id: Mapped[int] = mapped_column(ForeignKey("fragrances.id"), primary_key=True)
    warm: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    fresh: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    sweet: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    dark: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    woody: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    floral: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    spicy: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    fruit: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    green: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    aquatic: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    marine: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    leather: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    powdery: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    resinous: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    smoky: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    gourmand: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    citrus: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    aromatic: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    luxury: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    projection: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    longevity: Mapped[Decimal] = mapped_column(Numeric(4, 3))
