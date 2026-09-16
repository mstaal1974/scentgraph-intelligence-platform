from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from aromatwin.database import Base


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    note_type: Mapped[str]
    description: Mapped[str | None] = mapped_column(Text)
