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
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CzechMatchReason


class AudioStream(Base):
    __tablename__ = "audio_streams"
    __table_args__ = (
        UniqueConstraint(
            "media_file_id",
            "stream_index",
            name="uq_audio_streams_file_stream_index",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    media_file_id: Mapped[int] = mapped_column(
        ForeignKey("media_files.id"),
        index=True,
        nullable=False,
    )
    stream_index: Mapped[int] = mapped_column(Integer, nullable=False)
    codec_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    codec_long_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channel_layout: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bit_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_language: Mapped[str | None] = mapped_column(String(120), nullable=True)
    normalized_language: Mapped[str | None] = mapped_column(String(120), nullable=True)
    original_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    czech_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    match_reason: Mapped[CzechMatchReason] = mapped_column(
        String(80),
        default=CzechMatchReason.NO_MATCH,
        nullable=False,
    )
    matched_value: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
