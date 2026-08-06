from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IgnoredObjectType


class IgnoredItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_type: IgnoredObjectType
    object_id: int = Field(ge=1)
    reason: str | None = Field(default=None, max_length=1000)


class IgnoredItemRead(IgnoredItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
