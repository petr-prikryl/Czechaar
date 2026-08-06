from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ScanRunStatus


class CurrentScanProgress(BaseModel):
    scan_run_id: int
    status: ScanRunStatus
    completed_item_count: int
    requested_item_count: int
    current_status: str | None


class DashboardStats(BaseModel):
    total_movies: int
    total_episodes: int
    total_media_files: int
    scanned_files: int
    files_with_czech_audio: int
    files_missing_czech_audio: int
    scan_errors: int
    files_without_mappings: int
    ignored_items: int
    stale_items: int
    last_synchronization_time: datetime | None
    last_completed_scan_time: datetime | None
    current_scan: CurrentScanProgress | None
