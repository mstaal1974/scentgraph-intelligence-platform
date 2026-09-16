from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class SupplierOffer(Base):
    __tablename__ = "supplier_offers"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_name: Mapped[str]
    supplier_file_reference: Mapped[str]
    supplier_file_hash: Mapped[str]
    supplier_row_number: Mapped[int]
    supplier_brand_raw: Mapped[str] = mapped_column(Text)
    supplier_name_raw: Mapped[str] = mapped_column(Text)
    supplier_reference_raw: Mapped[str | None] = mapped_column(Text)
    supplier_code_private: Mapped[str | None]
    supplier_cn_code_private: Mapped[str | None]
    supplier_unit: Mapped[str | None]
    quantity_private: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    price_aed_private: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    price_usd_private: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None]
    price_basis: Mapped[str | None]
    normalised_brand: Mapped[str]
    normalised_name: Mapped[str]
    normalised_reference: Mapped[str | None]
    candidate_brand: Mapped[str | None]
    candidate_fragrance_name: Mapped[str | None]
    linked_match_candidate_id: Mapped[int | None] = mapped_column(ForeignKey("match_candidates.id"))
    linked_catalogue_fragrance_id: Mapped[int | None] = mapped_column(ForeignKey("fragrances.id"))
    offer_status: Mapped[str]
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    review_status: Mapped[str]
    private_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                   onupdate=func.now())
