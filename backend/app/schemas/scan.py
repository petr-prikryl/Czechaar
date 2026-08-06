from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ScanRunStatus, ScanState, ScanType, SourceType


class ScanStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scan_type: ScanType = ScanType.FULL
    source_type: SourceType | None = None
    integration_id: int | None = Field(default=None, ge=1)
    media_item_id: int | None = Field(default=None, ge=1)
    media_file_id: int | None = Field(default=None, ge=1)
    force: bool = False


class ScanRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_type: ScanType
    source_type: SourceType | None
    integration_id: int | None
    status: ScanRunStatus
    requested_item_count: int
    completed_item_count: int
    success_count: int
    missing_czech_count: int
    cache_hit_count: int
    error_count: int
    cancellation_requested: bool
    current_status: str | None
    error_summary: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class ScanRunItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_run_id: int
    media_file_id: int
    status: ScanState
    cache_hit: bool
    error_code: str | None
    started_at: datetime | None
    finished_at: datetime | None


class ScanProgressResponse(BaseModel):
    run: ScanRunRead
    items: list[ScanRunItemRead]
