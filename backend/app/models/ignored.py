from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import IgnoredObjectType


class IgnoredItem(Base):
    __tablename__ = "ignored_items"
    __table_args__ = (UniqueConstraint("object_type", "object_id", name="uq_ignored_items_object"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    object_type: Mapped[IgnoredObjectType] = mapped_column(String(40), nullable=False)
    object_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
