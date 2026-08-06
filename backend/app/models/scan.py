from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ScanRunStatus, ScanState, ScanType, SourceType


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_type: Mapped[ScanType] = mapped_column(String(40), index=True, nullable=False)
    source_type: Mapped[SourceType | None] = mapped_column(String(20), index=True, nullable=True)
    integration_id: Mapped[int | None] = mapped_column(
        ForeignKey("integrations.id"),
        index=True,
        nullable=True,
    )
    status: Mapped[ScanRunStatus] = mapped_column(
        String(40),
        default=ScanRunStatus.QUEUED,
        index=True,
        nullable=False,
    )
    requested_item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_czech_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cache_hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancellation_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_status: Mapped[str | None] = mapped_column(String(300), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScanRunItem(Base):
    __tablename__ = "scan_run_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_run_id: Mapped[int] = mapped_column(
        ForeignKey("scan_runs.id"),
        index=True,
        nullable=False,
    )
    media_file_id: Mapped[int] = mapped_column(
        ForeignKey("media_files.id"),
        index=True,
        nullable=False,
    )
    status: Mapped[ScanState] = mapped_column(String(80), default=ScanState.QUEUED, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
