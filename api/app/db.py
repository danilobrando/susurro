"""Database session — single Postgres engine, dependency-injected per request."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .settings import get_settings


def _normalize_database_url(url: str) -> str:
    """Railway / Heroku give `postgres://` URLs; SQLAlchemy 2.x wants `postgresql+psycopg://`."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


settings = get_settings()
DATABASE_URL = _normalize_database_url(settings.database_url)

# SQLite needs the `check_same_thread` kwarg for FastAPI's threaded request handling;
# Postgres doesn't. Keep the engine creation conditional so dev mode (SQLite) still works.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


def init_db() -> None:
    """Create tables if they don't exist. Called once at app startup."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
