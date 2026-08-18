from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.db.session import SessionLocal, initialize_database
from app.models.enums import ScanRunStatus, ScanType, SourceType
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.models.scan import ScanRun, ScanRunItem
from app.schemas.scan import ScanStartRequest
from app.services.scan_engine import ScanEngine, recover_interrupted_scans, scan_runner


def reset_scans() -> None:
    initialize_database()
    with SessionLocal() as session:
        session.query(ScanRunItem).delete()
        session.query(ScanRun).delete()
        session.query(MediaItemFileLink).delete()
        session.query(MediaItem).delete()
        session.query(MediaFile).delete()
        session.query(Integration).delete()
        session.commit()


def add_scan_file() -> int:
    with SessionLocal() as session:
        integration = Integration(
            source_type=SourceType.RADARR,
            name="Radarr",
            base_url="https://radarr.test",
            api_key="key",
            enabled=True,
            timeout_seconds=10,
            verify_tls=True,
        )
        session.add(integration)
        session.flush()
        media_file = MediaFile(
            integration_id=integration.id,
            source_type=SourceType.RADARR,
            external_file_id="20",
            original_source_path="/data/movie.mkv",
        )
        session.add(media_file)
        session.commit()
        return media_file.id


def test_scan_creation_persists_run_and_items() -> None:
    reset_scans()
    media_file_id = add_scan_file()

    with SessionLocal() as session:
        run, file_ids, force = ScanEngine(session).create_scan(
            ScanStartRequest(
                scan_type=ScanType.MEDIA_FILE, media_file_id=media_file_id, force=True
            ),
            force=True,
        )

        assert run.requested_item_count == 1
        assert file_ids == [media_file_id]
        assert force is True
        assert session.query(ScanRunItem).count() == 1


def test_series_scan_selects_only_matching_series_files() -> None:
    reset_scans()
    with SessionLocal() as session:
        integration = Integration(
            source_type=SourceType.SONARR,
            name="Sonarr",
            base_url="https://sonarr.test",
            api_key="key",
            enabled=True,
            timeout_seconds=10,
            verify_tls=True,
        )
        session.add(integration)
        session.flush()
        matching_file = MediaFile(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            external_file_id="100",
            original_source_path="/tv/demo/s01e01.mkv",
        )
        other_file = MediaFile(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            external_file_id="200",
            original_source_path="/tv/other/s01e01.mkv",
        )
        session.add_all([matching_file, other_file])
        session.flush()
        matching_episode = MediaItem(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            external_item_id="101",
            external_series_id="7",
            media_type="episode",
            title="Part One",
            monitored=True,
            file_presence=True,
        )
        other_episode = MediaItem(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            external_item_id="201",
            external_series_id="8",
            media_type="episode",
            title="Other",
            monitored=True,
            file_presence=True,
        )
        session.add_all([matching_episode, other_episode])
        session.flush()
        session.add_all(
            [
                MediaItemFileLink(
                    media_item_id=matching_episode.id,
                    media_file_id=matching_file.id,
                ),
                MediaItemFileLink(media_item_id=other_episode.id, media_file_id=other_file.id),
            ]
        )
        session.commit()
        integration_id = integration.id
        matching_file_id = matching_file.id

    with SessionLocal() as session:
        run, file_ids, _ = ScanEngine(session).create_scan(
            ScanStartRequest(
                scan_type=ScanType.SERIES,
                integration_id=integration_id,
                external_series_id="7",
                force=True,
            ),
            force=True,
        )

        assert run.requested_item_count == 1
        assert file_ids == [matching_file_id]


@pytest.mark.asyncio
async def test_empty_scan_finishes_with_no_media_diagnostic() -> None:
    reset_scans()

    with SessionLocal() as session:
        run, file_ids, force = ScanEngine(session).create_scan(
            ScanStartRequest(scan_type=ScanType.FULL),
            force=False,
        )

    assert file_ids == []
    assert force is False

    await scan_runner.run(run.id, file_ids, force=force)

    with SessionLocal() as session:
        refreshed = session.get(ScanRun, run.id)
        assert refreshed is not None
        assert refreshed.status == ScanRunStatus.COMPLETED
        assert refreshed.requested_item_count == 0
        assert refreshed.completed_item_count == 0
        assert refreshed.current_status == "no_media_files"
        assert refreshed.finished_at is not None


def test_scan_cancellation_sets_persistent_flag() -> None:
    reset_scans()
    media_file_id = add_scan_file()
    with SessionLocal() as session:
        run, _, _ = ScanEngine(session).create_scan(
            ScanStartRequest(scan_type=ScanType.MEDIA_FILE, media_file_id=media_file_id),
            force=False,
        )

    assert scan_runner.cancel(run.id) is True
    with SessionLocal() as session:
        refreshed = session.get(ScanRun, run.id)
        assert refreshed is not None
        assert refreshed.cancellation_requested is True
        assert refreshed.status == ScanRunStatus.CANCELLING


def test_interrupted_scan_recovery() -> None:
    reset_scans()
    with SessionLocal() as session:
        run = ScanRun(
            scan_type=ScanType.FULL,
            status=ScanRunStatus.RUNNING,
            requested_item_count=3,
            started_at=datetime.now(UTC),
        )
        session.add(run)
        session.commit()

    recover_interrupted_scans()

    with SessionLocal() as session:
        recovered = session.query(ScanRun).one()
        assert recovered.status == ScanRunStatus.INTERRUPTED
        assert recovered.finished_at is not None
