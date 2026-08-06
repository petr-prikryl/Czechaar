from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.db.session import SessionLocal
from app.models.enums import ScanType
from app.schemas.scan import ScanStartRequest
from app.services.scan_engine import ScanEngine, scan_runner


class ScheduledScanWorker:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if not self.settings.scheduled_scan_enabled or self._task is not None:
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task

    def next_run_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(minutes=self.settings.scheduled_scan_interval_minutes)

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.settings.scheduled_scan_interval_minutes * 60,
                )
            except TimeoutError:
                await self._start_scheduled_scan()

    async def _start_scheduled_scan(self) -> None:
        with SessionLocal() as session:
            request = ScanStartRequest(scan_type=ScanType.SCHEDULED)
            run, file_ids, force = ScanEngine(session).create_scan(request, force=False)
        await scan_runner.run(run.id, file_ids, force=force)
