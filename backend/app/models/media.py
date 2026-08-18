from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MediaType, ScanState, SourceType


class MediaItem(Base):
    __tablename__ = "media_items"
    __table_args__ = (
        UniqueConstraint(
            "integration_id",
            "media_type",
            "external_item_id",
            name="uq_media_items_integration_media_external",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    integration_id: Mapped[int] = mapped_column(
        ForeignKey("integrations.id"), index=True, nullable=False
    )
    source_type: Mapped[SourceType] = mapped_column(String(20), index=True, nullable=False)
    external_item_id: Mapped[str] = mapped_column(String(80), nullable=False)
    external_series_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    external_tmdb_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    external_web_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_type: Mapped[MediaType] = mapped_column(String(20), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    series_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    absolute_episode_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monitored: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    file_presence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    upstream_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    poster_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    stale: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    file_links: Mapped[list[MediaItemFileLink]] = relationship(
        back_populates="media_item",
        cascade="all, delete-orphan",
    )


class MediaFile(Base):
    __tablename__ = "media_files"
    __table_args__ = (
        UniqueConstraint(
            "integration_id",
            "external_file_id",
            name="uq_media_files_integration_external",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    integration_id: Mapped[int] = mapped_column(
        ForeignKey("integrations.id"), index=True, nullable=False
    )
    source_type: Mapped[SourceType] = mapped_column(String(20), index=True, nullable=False)
    external_file_id: Mapped[str] = mapped_column(String(80), nullable=False)
    original_source_path: Mapped[str] = mapped_column(Text, nullable=False)
    mapped_local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    relative_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    modified_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    quality: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quality_profile: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scan_state: Mapped[ScanState] = mapped_column(
        String(80),
        default=ScanState.NOT_SCANNED,
        index=True,
        nullable=False,
    )
    czech_audio_result: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    analyzer_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_successful_scan: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_scan_attempt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sanitized_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stale: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    item_links: Mapped[list[MediaItemFileLink]] = relationship(
        back_populates="media_file",
        cascade="all, delete-orphan",
    )


class MediaItemFileLink(Base):
    __tablename__ = "media_item_file_links"
    __table_args__ = (
        UniqueConstraint(
            "media_item_id", "media_file_id", name="uq_media_item_file_links_item_file"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    media_item_id: Mapped[int] = mapped_column(
        ForeignKey("media_items.id"), index=True, nullable=False
    )
    media_file_id: Mapped[int] = mapped_column(
        ForeignKey("media_files.id"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    media_item: Mapped[MediaItem] = relationship(back_populates="file_links")
    media_file: Mapped[MediaFile] = relationship(back_populates="item_links")
