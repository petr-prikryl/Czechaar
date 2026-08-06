from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SourceType, SyncStatus


class LibrarySyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType | None = None
    integration_id: int | None = Field(default=None, ge=1)


class LibrarySyncRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: SourceType | None
    integration_id: int | None
    status: SyncStatus
    started_at: datetime
    finished_at: datetime | None
    items_total: int
    files_total: int
    stale_count: int
    error_message: str | None
