from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.db.session import get_session
from app.models.enums import MediaType, ScanRunStatus, ScanState, SyncStatus
from app.models.ignored import IgnoredItem
from app.models.media import MediaFile, MediaItem
from app.models.scan import ScanRun
from app.models.sync import LibrarySyncRun
from app.schemas.dashboard import CurrentScanProgress, DashboardStats

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(session: Session = Depends(get_session)) -> DashboardStats:
    total_movies = _count(
        session, select(func.count()).where(MediaItem.media_type == MediaType.MOVIE)
    )
    total_episodes = _count(
        session, select(func.count()).where(MediaItem.media_type == MediaType.EPISODE)
    )
    total_files = _count(session, select(func.count()).select_from(MediaFile))
    scanned_files = _count(
        session,
        select(func.count()).where(
            MediaFile.scan_state.in_([ScanState.CZECH_AUDIO_FOUND, ScanState.CZECH_AUDIO_MISSING])
        ),
    )
    files_with_czech = _count(
        session,
        select(func.count()).where(MediaFile.scan_state == ScanState.CZECH_AUDIO_FOUND),
    )
    files_missing_czech = _count(
        session,
        select(func.count()).where(MediaFile.scan_state == ScanState.CZECH_AUDIO_MISSING),
    )
    scan_errors = _count(
        session,
        select(func.count()).where(
            MediaFile.scan_state.in_(
                [
                    ScanState.FILE_MISSING,
                    ScanState.PATH_NOT_MAPPED,
                    ScanState.PATH_OUTSIDE_ALLOWED_ROOTS,
                    ScanState.PATH_INACCESSIBLE,
                    ScanState.FFPROBE_NOT_AVAILABLE,
                    ScanState.FFPROBE_TIMEOUT,
                    ScanState.FFPROBE_INVALID_OUTPUT,
                    ScanState.FFPROBE_EXECUTION_ERROR,
                ]
            )
        ),
    )
    files_without_mappings = _count(
        session,
        select(func.count()).where(MediaFile.scan_state == ScanState.PATH_NOT_MAPPED),
    )
    ignored_items = _count(session, select(func.count()).select_from(IgnoredItem))
    stale_items = _count(session, select(func.count()).where(MediaItem.stale.is_(True)))
    last_sync = session.scalar(
        select(LibrarySyncRun.finished_at)
        .where(LibrarySyncRun.status == SyncStatus.COMPLETED)
        .order_by(LibrarySyncRun.finished_at.desc())
        .limit(1)
    )
    last_scan = session.scalar(
        select(ScanRun.finished_at)
        .where(ScanRun.status == ScanRunStatus.COMPLETED)
        .order_by(ScanRun.finished_at.desc())
        .limit(1)
    )
    current_scan_run = session.scalar(
        select(ScanRun)
        .where(
            ScanRun.status.in_(
                [ScanRunStatus.QUEUED, ScanRunStatus.RUNNING, ScanRunStatus.CANCELLING]
            )
        )
        .order_by(ScanRun.created_at.desc())
        .limit(1)
    )
    current_scan = None
    if current_scan_run is not None:
        current_scan = CurrentScanProgress(
            scan_run_id=current_scan_run.id,
            status=current_scan_run.status,
            completed_item_count=current_scan_run.completed_item_count,
            requested_item_count=current_scan_run.requested_item_count,
            current_status=current_scan_run.current_status,
        )
    return DashboardStats(
        total_movies=total_movies,
        total_episodes=total_episodes,
        total_media_files=total_files,
        scanned_files=scanned_files,
        files_with_czech_audio=files_with_czech,
        files_missing_czech_audio=files_missing_czech,
        scan_errors=scan_errors,
        files_without_mappings=files_without_mappings,
        ignored_items=ignored_items,
        stale_items=stale_items,
        last_synchronization_time=last_sync,
        last_completed_scan_time=last_scan,
        current_scan=current_scan,
    )


def _count(session: Session, statement: Select[tuple[int]]) -> int:
    return int(session.scalar(statement) or 0)
