from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.config import Settings, get_settings
from app.db.base import Base


def build_engine(settings: Settings | None = None) -> Engine:
    active_settings = settings or get_settings()
    if active_settings.is_sqlite:
        active_settings.config_dir.mkdir(parents=True, exist_ok=True)

    connect_args = {"check_same_thread": False} if active_settings.is_sqlite else {}
    return create_engine(
        active_settings.resolved_database_url, connect_args=connect_args, future=True
    )


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def check_database() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
