from pathlib import Path

import pytest

from app.db.session import SessionLocal, initialize_database
from app.models.audio import AudioStream
from app.models.enums import ScanState, SourceType
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.models.path_mapping import AllowedMediaRoot, PathMapping
from app.models.scan import ScanRun, ScanRunItem
from app.models.sync import LibrarySyncRun
from app.services.ffprobe import FfprobeResult, FfprobeRunner
from app.services.media_analysis import MediaAnalysisService
from app.services.path_mapping import normalize_media_path


def reset_analysis_tables() -> None:
    initialize_database()
    with SessionLocal() as session:
        session.query(AudioStream).delete()
        session.query(ScanRunItem).delete()
        session.query(ScanRun).delete()
        session.query(MediaItemFileLink).delete()
        session.query(MediaFile).delete()
        session.query(MediaItem).delete()
        session.query(PathMapping).delete()
        session.query(AllowedMediaRoot).delete()
        session.query(LibrarySyncRun).delete()
        session.query(Integration).delete()
        session.commit()


def add_media_file(path: Path) -> int:
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
            original_source_path=str(path),
        )
        session.add(media_file)
        session.commit()
        return media_file.id


@pytest.mark.asyncio
async def test_analysis_uses_original_path_inside_allowed_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_analysis_tables()
    media_root = tmp_path / "movies"
    media_root.mkdir()
    media_path = media_root / "Avatar.mkv"
    media_path.write_bytes(b"fake media")
    media_file_id = add_media_file(media_path)
    inspected_paths: list[Path] = []

    async def fake_inspect(
        self: FfprobeRunner,
        path: Path,
    ) -> FfprobeResult:
        inspected_paths.append(path)
        return FfprobeResult(ScanState.CZECH_AUDIO_MISSING, [])

    monkeypatch.setattr(FfprobeRunner, "inspect_audio_streams", fake_inspect)

    with SessionLocal() as session:
        session.add(AllowedMediaRoot(path=str(media_root), enabled=True))
        session.commit()
        outcome = await MediaAnalysisService(session).analyze_media_file(media_file_id, force=True)

    assert inspected_paths == [media_path]
    assert outcome.media_file.mapped_local_path == normalize_media_path(str(media_path))
    assert outcome.media_file.scan_state == ScanState.CZECH_AUDIO_MISSING
    assert outcome.media_file.error_code is None


@pytest.mark.asyncio
async def test_analysis_rejects_unmapped_path_outside_allowed_roots(tmp_path: Path) -> None:
    reset_analysis_tables()
    media_root = tmp_path / "movies"
    outside_root = tmp_path / "downloads"
    media_root.mkdir()
    outside_root.mkdir()
    media_path = outside_root / "Avatar.mkv"
    media_path.write_bytes(b"fake media")
    media_file_id = add_media_file(media_path)

    with SessionLocal() as session:
        session.add(AllowedMediaRoot(path=str(media_root), enabled=True))
        session.commit()
        outcome = await MediaAnalysisService(session).analyze_media_file(media_file_id, force=True)

    assert outcome.media_file.mapped_local_path is None
    assert outcome.media_file.scan_state == ScanState.PATH_NOT_MAPPED
    assert outcome.media_file.error_code == ScanState.PATH_NOT_MAPPED
