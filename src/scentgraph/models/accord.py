from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from scentgraph.database import Base


class Accord(Base):
    __tablename__ = "accords"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None] = mapped_column(Text)
