from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class CloneRelationship(Base):
    __tablename__ = "clone_relationships"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_item_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_items.id"))
    clone_fragrance_id: Mapped[int | None] = mapped_column(ForeignKey("fragrances.id"))
    original_fragrance_id: Mapped[int] = mapped_column(ForeignKey("fragrances.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    relationship_type: Mapped[str]
    similarity_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    score_status: Mapped[str] = mapped_column(default="estimated")
    difference_summary: Mapped[str | None] = mapped_column(Text)
    performance_notes: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(ForeignKey("review_statuses.code"))
