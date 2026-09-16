from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    supplier_name: Mapped[str]
    source_file: Mapped[str]
    source_sha256: Mapped[str]
    row_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(ForeignKey("review_statuses.code"))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SupplierItem(Base):
    __tablename__ = "supplier_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_name: Mapped[str]
    supplier_brand_raw: Mapped[str] = mapped_column(Text)
    supplier_name_raw: Mapped[str] = mapped_column(Text)
    supplier_ori_raw: Mapped[str | None] = mapped_column(Text)
    supplier_cn_code: Mapped[str | None]
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    aed_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    usd_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    source_file: Mapped[str]
    source_row_number: Mapped[int]
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    import_batch_id: Mapped[UUID] = mapped_column(ForeignKey("import_batches.id"))
    normalised_brand: Mapped[str]
    normalised_name: Mapped[str]
    variant_marker: Mapped[str | None]
    status: Mapped[str] = mapped_column(ForeignKey("review_statuses.code"))
