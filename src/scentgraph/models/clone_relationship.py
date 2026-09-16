from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from scentgraph.database import Base


class CloneRelationship(Base):
    __tablename__ = "clone_relationships"
    id: Mapped[int] = mapped_column(primary_key=True)
    clone_fragrance_id: Mapped[int] = mapped_column(ForeignKey("fragrances.id"))
    original_fragrance_id: Mapped[int] = mapped_column(ForeignKey("fragrances.id"))
    relationship_type: Mapped[str]
    similarity_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    performance_difference: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    longevity_difference: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    projection_difference: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    price_difference: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)
