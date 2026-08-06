from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import SourceType, SyncStatus


class LibrarySyncRun(Base):
    __tablename__ = "library_sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[SourceType | None] = mapped_column(String(20), index=True, nullable=True)
    integration_id: Mapped[int | None] = mapped_column(
        ForeignKey("integrations.id"), index=True, nullable=True
    )
    status: Mapped[SyncStatus] = mapped_column(
        String(20), default=SyncStatus.RUNNING, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    items_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stale_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
