"""SQLAlchemy engine and session factory for Aegis AI."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def _get_database_url() -> str:
    """Read DATABASE_URL from settings or environment."""
    try:
        from aegis.config import get_settings

        return get_settings().database_url
    except Exception:
        return "sqlite:///aegis.db"


def get_engine() -> Engine:
    """Return (or create) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        url = _get_database_url()
        connect_args: dict[str, Any] = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(url, connect_args=connect_args, echo=False)

        # Enable WAL mode for SQLite to improve concurrency
        if url.startswith("sqlite"):

            @event.listens_for(_engine, "connect")
            def set_wal(dbapi_conn: Any, _: object) -> None:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return (or create) the session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(
            bind=get_engine(),
            class_=Session,
            expire_on_commit=False,
        )
    return _SessionFactory


def init_db() -> None:
    """Create all tables if they don't exist."""
    from aegis.db import models as _  # noqa: F401 - ensure models are registered

    Base.metadata.create_all(bind=get_engine())


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager providing a database session with auto-commit/rollback."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
