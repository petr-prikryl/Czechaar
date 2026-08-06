from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
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
    _ensure_sqlite_compatibility_schema()


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


def _ensure_sqlite_compatibility_schema() -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "integrations" in tables:
            columns = {column["name"] for column in inspector.get_columns("integrations")}
            if "web_url" not in columns:
                connection.execute(text("ALTER TABLE integrations ADD COLUMN web_url VARCHAR(500)"))
        if "media_items" in tables:
            columns = {column["name"] for column in inspector.get_columns("media_items")}
            if "external_web_path" not in columns:
                connection.execute(
                    text("ALTER TABLE media_items ADD COLUMN external_web_path VARCHAR(500)")
                )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_media_items_series_season "
                    "ON media_items (integration_id, external_series_id, season_number)"
                )
            )
        if "media_files" in tables:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_media_files_missing_listing "
                    "ON media_files (scan_state, stale, integration_id)"
                )
            )
