from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from scentgraph.database import Base


class Provenance(Base):
    __tablename__ = "source_provenance"
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str]
    entity_id: Mapped[int]
    source_name: Mapped[str]
    source_type: Mapped[str]
    source_reference: Mapped[str | None]
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
