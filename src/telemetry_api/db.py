"""Database engine, session factory, and the FastAPI session dependency.

The engine is built lazily from settings so tests can point ``DATABASE_URL`` at
a temporary database before anything connects.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _connect_args(url: str) -> dict:
    # SQLite + a threaded server needs this flag
    return {"check_same_thread": False} if url.startswith("sqlite") else {}


def init_engine(url: str | None = None):
    """Create (or recreate) the engine and session factory and the schema."""
    global _engine, _SessionLocal
    url = url or get_settings().database_url
    _engine = create_engine(url, connect_args=_connect_args(url), future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session and always closing it."""
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
