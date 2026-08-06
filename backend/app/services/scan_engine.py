from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import MediaType, ScanRunStatus, ScanState, ScanType, SourceType
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.models.scan import ScanRun, ScanRunItem
from app.schemas.scan import ScanStartRequest
from app.services.media_analysis import MediaAnalysisService

SUCCESS_STATES = {ScanState.CZECH_AUDIO_FOUND, ScanState.CZECH_AUDIO_MISSING}
ERROR_STATES = {
    ScanState.FILE_MISSING,
    ScanState.PATH_NOT_MAPPED,
    ScanState.PATH_OUTSIDE_ALLOWED_ROOTS,
    ScanState.PATH_INACCESSIBLE,
    ScanState.FFPROBE_NOT_AVAILABLE,
    ScanState.FFPROBE_TIMEOUT,
    ScanState.FFPROBE_INVALID_OUTPUT,
    ScanState.FFPROBE_EXECUTION_ERROR,
}


class ScanEngine:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_scan(
        self,
        request: ScanStartRequest,
        *,
        force: bool = False,
    ) -> tuple[ScanRun, list[int], bool]:
        scan_type = request.scan_type
        source_type = request.source_type
        integration_id = request.integration_id
        media_item_id = request.media_item_id
        media_file_id = request.media_file_id
        file_ids = self._select_media_file_ids(
            scan_type=scan_type,
            source_type=source_type,
            integration_id=integration_id,
            media_item_id=media_item_id,
            media_file_id=media_file_id,
        )
        run = ScanRun(
            scan_type=scan_type,
            source_type=source_type,
            integration_id=integration_id,
            requested_item_count=len(file_ids),
            current_status="queued",
        )
        self.session.add(run)
        self.session.flush()
        for file_id in file_ids:
            self.session.add(ScanRunItem(scan_run_id=run.id, media_file_id=file_id))
        self.session.commit()
        self.session.refresh(run)
        return run, file_ids, force

    def _select_media_file_ids(
        self,
        *,
        scan_type: ScanType,
        source_type: SourceType | None,
        integration_id: int | None,
        media_item_id: int | None,
        media_file_id: int | None,
    ) -> list[int]:
        if scan_type == ScanType.MEDIA_FILE:
            return [media_file_id] if media_file_id is not None else []
        statement = select(MediaFile.id).where(MediaFile.stale.is_(False))
        if scan_type == ScanType.RADARR:
            statement = statement.where(MediaFile.source_type == SourceType.RADARR)
        if scan_type == ScanType.SONARR:
            statement = statement.where(MediaFile.source_type == SourceType.SONARR)
        if scan_type == ScanType.INTEGRATION and integration_id is not None:
            statement = statement.where(MediaFile.integration_id == integration_id)
        if source_type is not None:
            statement = statement.where(MediaFile.source_type == source_type)
        if media_item_id is not None:
            statement = (
                statement.join(MediaItemFileLink, MediaItemFileLink.media_file_id == MediaFile.id)
                .join(MediaItem, MediaItem.id == MediaItemFileLink.media_item_id)
                .where(MediaItem.id == media_item_id)
            )
        if scan_type == ScanType.MOVIE:
            statement = (
                statement.join(MediaItemFileLink, MediaItemFileLink.media_file_id == MediaFile.id)
                .join(MediaItem, MediaItem.id == MediaItemFileLink.media_item_id)
                .where(MediaItem.media_type == MediaType.MOVIE)
            )
        if scan_type == ScanType.EPISODE:
            statement = (
                statement.join(MediaItemFileLink, MediaItemFileLink.media_file_id == MediaFile.id)
                .join(MediaItem, MediaItem.id == MediaItemFileLink.media_item_id)
                .where(MediaItem.media_type == MediaType.EPISODE)
            )
        if scan_type == ScanType.FULL:
            statement = statement.where(
                or_(
                    MediaFile.source_type == SourceType.RADARR,
                    MediaFile.source_type == SourceType.SONARR,
                )
            )
        return list(dict.fromkeys(self.session.scalars(statement.order_by(MediaFile.id))))


class ScanRunner:
    def __init__(self) -> None:
        self._cancel_events: dict[int, asyncio.Event] = {}

    async def run(self, run_id: int, file_ids: list[int], *, force: bool) -> None:
        settings = get_settings()
        concurrency = max(1, settings.scan_concurrency)
        semaphore = asyncio.Semaphore(concurrency)
        cancel_event = self._cancel_events.setdefault(run_id, asyncio.Event())
        self._mark_run_started(run_id)

        if not file_ids:
            self._finish_run(run_id)
            self._cancel_events.pop(run_id, None)
            return

        async def process(file_id: int) -> None:
            async with semaphore:
                if cancel_event.is_set() or self._cancellation_requested(run_id):
                    self._mark_item_cancelled(run_id, file_id)
                    return
                await self._process_file(run_id, file_id, force=force)

        await asyncio.gather(*(process(file_id) for file_id in file_ids))
        self._finish_run(run_id)
        self._cancel_events.pop(run_id, None)

    def cancel(self, run_id: int) -> bool:
        with SessionLocal() as session:
            run = session.get(ScanRun, run_id)
            if run is None:
                return False
            run.cancellation_requested = True
            run.status = ScanRunStatus.CANCELLING
            run.current_status = "cancellation requested"
            session.add(run)
            session.commit()
        event = self._cancel_events.setdefault(run_id, asyncio.Event())
        event.set()
        return True

    def _mark_run_started(self, run_id: int) -> None:
        with SessionLocal() as session:
            run = session.get(ScanRun, run_id)
            if run is None:
                return
            run.status = ScanRunStatus.RUNNING
            run.started_at = datetime.now(UTC)
            run.current_status = "scanning"
            session.add(run)
            session.commit()

    def _cancellation_requested(self, run_id: int) -> bool:
        with SessionLocal() as session:
            run = session.get(ScanRun, run_id)
            return bool(run and run.cancellation_requested)

    async def _process_file(self, run_id: int, file_id: int, *, force: bool) -> None:
        with SessionLocal() as session:
            item = session.scalar(
                select(ScanRunItem).where(
                    ScanRunItem.scan_run_id == run_id,
                    ScanRunItem.media_file_id == file_id,
                )
            )
            if item is None:
                return
            item.status = ScanState.SCANNING
            item.started_at = datetime.now(UTC)
            session.add(item)
            session.commit()

        with SessionLocal() as session:
            outcome = await MediaAnalysisService(session).analyze_media_file(file_id, force=force)
            media_file = outcome.media_file
            status_value = media_file.scan_state
            error_code = media_file.error_code
            cache_hit = outcome.cache_hit

        with SessionLocal() as session:
            item = session.scalar(
                select(ScanRunItem).where(
                    ScanRunItem.scan_run_id == run_id,
                    ScanRunItem.media_file_id == file_id,
                )
            )
            run = session.get(ScanRun, run_id)
            if item is None or run is None:
                return
            item.status = status_value
            item.cache_hit = cache_hit
            item.error_code = error_code
            item.finished_at = datetime.now(UTC)
            run.completed_item_count += 1
            if cache_hit:
                run.cache_hit_count += 1
            if status_value == ScanState.CZECH_AUDIO_FOUND:
                run.success_count += 1
            elif status_value == ScanState.CZECH_AUDIO_MISSING:
                run.missing_czech_count += 1
            elif status_value in ERROR_STATES:
                run.error_count += 1
            run.current_status = f"scanned {run.completed_item_count}/{run.requested_item_count}"
            session.add_all([item, run])
            session.commit()

    def _mark_item_cancelled(self, run_id: int, file_id: int) -> None:
        with SessionLocal() as session:
            item = session.scalar(
                select(ScanRunItem).where(
                    ScanRunItem.scan_run_id == run_id,
                    ScanRunItem.media_file_id == file_id,
                )
            )
            run = session.get(ScanRun, run_id)
            if item is None or run is None:
                return
            item.status = ScanState.CANCELLED
            item.finished_at = datetime.now(UTC)
            run.completed_item_count += 1
            session.add_all([item, run])
            session.commit()

    def _finish_run(self, run_id: int) -> None:
        with SessionLocal() as session:
            run = session.get(ScanRun, run_id)
            if run is None:
                return
            if run.cancellation_requested:
                run.status = ScanRunStatus.CANCELLED
                run.current_status = "cancelled"
            elif run.requested_item_count == 0:
                run.status = ScanRunStatus.COMPLETED
                run.current_status = "no_media_files"
            elif run.error_count > 0:
                run.status = ScanRunStatus.FAILED
                run.current_status = "completed with errors"
            else:
                run.status = ScanRunStatus.COMPLETED
                run.current_status = "completed"
            run.finished_at = datetime.now(UTC)
            session.add(run)
            session.commit()


scan_runner = ScanRunner()


def recover_interrupted_scans() -> None:
    with SessionLocal() as session:
        statement = select(ScanRun).where(
            ScanRun.status.in_(
                [
                    ScanRunStatus.QUEUED,
                    ScanRunStatus.RUNNING,
                    ScanRunStatus.CANCELLING,
                ]
            )
        )
        for run in session.scalars(statement):
            run.status = ScanRunStatus.INTERRUPTED
            run.finished_at = datetime.now(UTC)
            run.current_status = "interrupted during application restart"
            session.add(run)
        session.commit()
