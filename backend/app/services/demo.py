from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.audio import AudioStream
from app.models.enums import (
    CzechMatchReason,
    IgnoredObjectType,
    MediaType,
    ScanRunStatus,
    ScanState,
    ScanType,
    SourceType,
    SyncStatus,
)
from app.models.ignored import IgnoredItem
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.models.path_mapping import AllowedMediaRoot, PathMapping
from app.models.scan import ScanRun, ScanRunItem
from app.models.setting import ApplicationSetting
from app.models.sync import LibrarySyncRun

DEMO_SEED_VERSION = "2026-08-06.1"
DEMO_SEED_KEY = "demo_seed_version"


def seed_demo_data() -> None:
    """Seed deterministic demo data when demo mode is explicitly enabled."""

    now = datetime.now(UTC)
    with SessionLocal() as session:
        marker = session.get(ApplicationSetting, DEMO_SEED_KEY)
        if marker is not None and marker.value == DEMO_SEED_VERSION:
            return

        existing_demo = session.scalar(select(Integration).where(Integration.name == "Demo Radarr"))
        if existing_demo is not None:
            if marker is None:
                marker = ApplicationSetting(key=DEMO_SEED_KEY, value=DEMO_SEED_VERSION)
                session.add(marker)
            else:
                marker.value = DEMO_SEED_VERSION
            session.commit()
            return

        radarr = Integration(
            source_type=SourceType.RADARR,
            name="Demo Radarr",
            base_url="https://demo.radarr.invalid",
            api_key=None,
            enabled=False,
            timeout_seconds=10,
            verify_tls=True,
        )
        sonarr = Integration(
            source_type=SourceType.SONARR,
            name="Demo Sonarr",
            base_url="https://demo.sonarr.invalid",
            api_key=None,
            enabled=False,
            timeout_seconds=10,
            verify_tls=True,
        )
        session.add_all([radarr, sonarr])
        session.flush()

        session.add_all(
            [
                PathMapping(
                    source_type=SourceType.RADARR,
                    remote_path_prefix="/data/movies",
                    local_path_prefix="/movies",
                    enabled=True,
                    priority=10,
                    description="Demo movie path mapping",
                ),
                PathMapping(
                    source_type=SourceType.SONARR,
                    remote_path_prefix="/data/tv",
                    local_path_prefix="/tv",
                    enabled=True,
                    priority=10,
                    description="Demo TV path mapping",
                ),
            ]
        )
        if (
            session.scalar(select(AllowedMediaRoot).where(AllowedMediaRoot.path == "/movies"))
            is None
        ):
            session.add(
                AllowedMediaRoot(path="/movies", enabled=True, description="Demo movies root")
            )
        if session.scalar(select(AllowedMediaRoot).where(AllowedMediaRoot.path == "/tv")) is None:
            session.add(AllowedMediaRoot(path="/tv", enabled=True, description="Demo TV root"))

        movie_found = _movie(
            radarr.id,
            "100",
            "Demo Film With Czech Audio",
            2022,
            "/data/movies/Demo Film With Czech Audio (2022)/movie.mkv",
            "/movies/Demo Film With Czech Audio (2022)/movie.mkv",
            "1000",
            ScanState.CZECH_AUDIO_FOUND,
            True,
            now,
        )
        movie_missing = _movie(
            radarr.id,
            "101",
            "Demo Film Missing Czech Audio",
            2023,
            "/data/movies/Demo Film Missing Czech Audio (2023)/movie.mkv",
            "/movies/Demo Film Missing Czech Audio (2023)/movie.mkv",
            "1001",
            ScanState.CZECH_AUDIO_MISSING,
            False,
            now,
        )
        movie_unmapped = _movie(
            radarr.id,
            "102",
            "Demo Film With Unmapped Path",
            2024,
            "/remote/movies/Demo Film With Unmapped Path (2024)/movie.mkv",
            None,
            "1002",
            ScanState.PATH_NOT_MAPPED,
            None,
            now,
        )

        episode_a, episode_file = _episode(
            sonarr.id,
            "200",
            "300",
            "Demo Show",
            "The Missing Track",
            1,
            1,
            "/data/tv/Demo Show/Season 01/Demo Show - S01E01.mkv",
            "/tv/Demo Show/Season 01/Demo Show - S01E01.mkv",
            "2000",
            ScanState.CZECH_AUDIO_MISSING,
            False,
            now,
        )
        episode_b, multi_file = _episode(
            sonarr.id,
            "201",
            "301",
            "Demo Show",
            "Double Feature Part One",
            1,
            2,
            "/data/tv/Demo Show/Season 01/Demo Show - S01E02-E03.mkv",
            "/tv/Demo Show/Season 01/Demo Show - S01E02-E03.mkv",
            "2001",
            ScanState.CZECH_AUDIO_FOUND,
            True,
            now,
        )
        episode_c = MediaItem(
            integration_id=sonarr.id,
            source_type=SourceType.SONARR,
            external_item_id="202",
            external_series_id="300",
            media_type=MediaType.EPISODE,
            title="Double Feature Part Two",
            series_title="Demo Show",
            season_number=1,
            episode_number=3,
            monitored=True,
            file_presence=True,
            upstream_status="aired",
            poster_url=None,
        )
        error_item, error_file = _episode(
            sonarr.id,
            "203",
            "302",
            "Demo Show",
            "Unreadable File",
            1,
            4,
            "/data/tv/Demo Show/Season 01/Demo Show - S01E04.mkv",
            "/tv/Demo Show/Season 01/Demo Show - S01E04.mkv",
            "2002",
            ScanState.FFPROBE_EXECUTION_ERROR,
            None,
            now,
            error_code="ffprobe_execution_error",
            sanitized_error_message="ffprobe exited with a non-zero status",
        )

        session.add_all(
            [
                movie_found.item,
                movie_found.file,
                movie_missing.item,
                movie_missing.file,
                movie_unmapped.item,
                movie_unmapped.file,
                episode_a,
                episode_file,
                episode_b,
                episode_c,
                multi_file,
                error_item,
                error_file,
            ]
        )
        session.flush()
        _link(session, movie_found.item, movie_found.file)
        _link(session, movie_missing.item, movie_missing.file)
        _link(session, movie_unmapped.item, movie_unmapped.file)
        _link(session, episode_a, episode_file)
        _link(session, episode_b, multi_file)
        _link(session, episode_c, multi_file)
        _link(session, error_item, error_file)

        session.add_all(
            [
                AudioStream(
                    media_file_id=movie_found.file.id,
                    stream_index=1,
                    codec_name="aac",
                    codec_long_name="AAC",
                    channels=2,
                    channel_layout="stereo",
                    sample_rate=48000,
                    bit_rate=192000,
                    original_language="ces",
                    normalized_language="ces",
                    original_title="Czech",
                    normalized_title="czech",
                    czech_match=True,
                    match_reason=CzechMatchReason.LANGUAGE_CODE,
                    matched_value="ces",
                ),
                AudioStream(
                    media_file_id=movie_missing.file.id,
                    stream_index=1,
                    codec_name="ac3",
                    codec_long_name="AC-3",
                    channels=6,
                    channel_layout="5.1",
                    sample_rate=48000,
                    bit_rate=640000,
                    original_language="eng",
                    normalized_language="eng",
                    original_title="English 5.1",
                    normalized_title="english 5.1",
                    czech_match=False,
                    match_reason=CzechMatchReason.NO_MATCH,
                ),
                AudioStream(
                    media_file_id=multi_file.id,
                    stream_index=1,
                    codec_name="aac",
                    codec_long_name="AAC",
                    channels=2,
                    channel_layout="stereo",
                    sample_rate=48000,
                    bit_rate=192000,
                    original_language="und",
                    normalized_language="und",
                    original_title="Cesky dabing",
                    normalized_title="cesky dabing",
                    czech_match=True,
                    match_reason=CzechMatchReason.STREAM_TITLE,
                    matched_value="cesky dabing",
                ),
            ]
        )

        scan_run = ScanRun(
            scan_type=ScanType.FULL,
            status=ScanRunStatus.COMPLETED,
            requested_item_count=6,
            completed_item_count=6,
            success_count=2,
            missing_czech_count=2,
            cache_hit_count=1,
            error_count=2,
            current_status="Demo scan completed",
            started_at=now - timedelta(minutes=12),
            finished_at=now - timedelta(minutes=10),
        )
        sync_run = LibrarySyncRun(
            status=SyncStatus.COMPLETED,
            started_at=now - timedelta(minutes=15),
            finished_at=now - timedelta(minutes=14),
            items_total=6,
            files_total=5,
            stale_count=0,
        )
        session.add_all([scan_run, sync_run])
        session.flush()
        for media_file in [
            movie_found.file,
            movie_missing.file,
            movie_unmapped.file,
            episode_file,
            multi_file,
            error_file,
        ]:
            session.add(
                ScanRunItem(
                    scan_run_id=scan_run.id,
                    media_file_id=media_file.id,
                    status=media_file.scan_state,
                    cache_hit=media_file.fingerprint is not None,
                    error_code=media_file.error_code,
                    started_at=scan_run.started_at,
                    finished_at=scan_run.finished_at,
                )
            )

        session.add(
            IgnoredItem(
                object_type=IgnoredObjectType.MEDIA_ITEM,
                object_id=movie_unmapped.item.id,
                reason="Demo ignored item",
            )
        )
        if marker is None:
            session.add(ApplicationSetting(key=DEMO_SEED_KEY, value=DEMO_SEED_VERSION))
        else:
            marker.value = DEMO_SEED_VERSION
        session.commit()


class DemoMovie:
    def __init__(self, item: MediaItem, file: MediaFile) -> None:
        self.item = item
        self.file = file


def _movie(
    integration_id: int,
    item_id: str,
    title: str,
    year: int,
    source_path: str,
    mapped_path: str | None,
    file_id: str,
    scan_state: ScanState,
    czech_audio_result: bool | None,
    now: datetime,
    *,
    error_code: str | None = None,
    sanitized_error_message: str | None = None,
) -> DemoMovie:
    last_successful_scan = now - timedelta(minutes=10) if czech_audio_result is not None else None
    item = MediaItem(
        integration_id=integration_id,
        source_type=SourceType.RADARR,
        external_item_id=item_id,
        media_type=MediaType.MOVIE,
        title=title,
        original_title=title,
        year=year,
        monitored=True,
        file_presence=True,
        upstream_status="released",
        poster_url=None,
    )
    file = MediaFile(
        integration_id=integration_id,
        source_type=SourceType.RADARR,
        external_file_id=file_id,
        original_source_path=source_path,
        mapped_local_path=mapped_path,
        relative_path=source_path.rsplit("/", 1)[-1],
        size=2_147_483_648,
        modified_time=now - timedelta(days=1),
        quality="Bluray-1080p",
        quality_profile="HD-1080p",
        fingerprint=f"demo:{file_id}" if czech_audio_result is not None else None,
        scan_state=scan_state,
        czech_audio_result=czech_audio_result,
        analyzer_version="demo",
        last_successful_scan=last_successful_scan,
        last_scan_attempt=now - timedelta(minutes=10),
        error_code=error_code,
        sanitized_error_message=sanitized_error_message,
    )
    return DemoMovie(item=item, file=file)


def _episode(
    integration_id: int,
    item_id: str,
    series_id: str,
    series_title: str,
    episode_title: str,
    season: int,
    episode: int,
    source_path: str,
    mapped_path: str | None,
    file_id: str,
    scan_state: ScanState,
    czech_audio_result: bool | None,
    now: datetime,
    *,
    error_code: str | None = None,
    sanitized_error_message: str | None = None,
) -> tuple[MediaItem, MediaFile]:
    last_successful_scan = now - timedelta(minutes=10) if czech_audio_result is not None else None
    item = MediaItem(
        integration_id=integration_id,
        source_type=SourceType.SONARR,
        external_item_id=item_id,
        external_series_id=series_id,
        media_type=MediaType.EPISODE,
        title=episode_title,
        series_title=series_title,
        season_number=season,
        episode_number=episode,
        monitored=True,
        file_presence=True,
        upstream_status="aired",
        poster_url=None,
    )
    file = MediaFile(
        integration_id=integration_id,
        source_type=SourceType.SONARR,
        external_file_id=file_id,
        original_source_path=source_path,
        mapped_local_path=mapped_path,
        relative_path=source_path.rsplit("/", 1)[-1],
        size=734_003_200,
        modified_time=now - timedelta(days=2),
        quality="WEB-DL-1080p",
        quality_profile="HD-1080p",
        fingerprint=f"demo:{file_id}" if czech_audio_result is not None else None,
        scan_state=scan_state,
        czech_audio_result=czech_audio_result,
        analyzer_version="demo",
        last_successful_scan=last_successful_scan,
        last_scan_attempt=now - timedelta(minutes=10),
        error_code=error_code,
        sanitized_error_message=sanitized_error_message,
    )
    return item, file


def _link(session: Session, item: MediaItem, media_file: MediaFile) -> None:
    session.add(MediaItemFileLink(media_item_id=item.id, media_file_id=media_file.id))
