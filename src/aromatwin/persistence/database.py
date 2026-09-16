"""Database boundary for operational persistence.

Engine construction is explicit so importing the package never opens a production connection.
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from aromatwin.config import Settings, get_settings
from aromatwin.database import Base

LOCAL_DATABASE_URL = "sqlite:///data/private/aromatwin-persistence.db"


def persistence_database_url(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if settings.is_local and settings.database_url.startswith("postgresql"):
        return LOCAL_DATABASE_URL
    return settings.database_url


def create_persistence_engine(
    database_url: str | None = None, *, settings: Settings | None = None
) -> Engine:
    url = database_url or persistence_database_url(settings)
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if url in {"sqlite://", "sqlite:///:memory:"}:
        kwargs.update(connect_args={"check_same_thread": False}, poolclass=StaticPool)
    elif url.startswith("sqlite:///"):
        path = Path(url.removeprefix("sqlite:///"))
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def transaction(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = factory()
    try:
        with session.begin():
            yield session
    finally:
        session.close()


def initialise_persistence(engine: Engine) -> None:
    """Create missing tables without dropping or replacing any existing table."""
    from aromatwin.persistence import models  # noqa: F401

    Base.metadata.create_all(engine)
