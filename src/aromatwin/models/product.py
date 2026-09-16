from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    fragrance_id: Mapped[int | None] = mapped_column(ForeignKey("fragrances.id"))
    supplier_item_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_items.id"))
    brand_owner: Mapped[str]
    product_name: Mapped[str]
    product_type: Mapped[str | None]
    size_ml: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    sku: Mapped[str]
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
