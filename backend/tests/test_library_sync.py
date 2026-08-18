from __future__ import annotations

import httpx
import pytest

from app.db.session import SessionLocal, initialize_database
from app.models.enums import MediaType, SourceType
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.models.sync import LibrarySyncRun
from app.services.library_sync import LibrarySyncService


def reset_library() -> None:
    initialize_database()
    with SessionLocal() as session:
        session.query(MediaItemFileLink).delete()
        session.query(MediaFile).delete()
        session.query(MediaItem).delete()
        session.query(LibrarySyncRun).delete()
        session.query(Integration).delete()
        session.commit()


def add_integration(source_type: SourceType) -> Integration:
    with SessionLocal() as session:
        integration = Integration(
            source_type=source_type,
            name=f"Test {source_type.value}",
            base_url=f"https://{source_type.value}.test",
            api_key="test-key",
            enabled=True,
            timeout_seconds=10,
            verify_tls=True,
        )
        session.add(integration)
        session.commit()
        session.refresh(integration)
        session.expunge(integration)
        return integration


@pytest.mark.asyncio
async def test_radarr_sync_imports_movie_and_file() -> None:
    reset_library()
    integration = add_integration(SourceType.RADARR)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Api-Key"] == "test-key"
        assert request.url.path == "/api/v3/movie"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 10,
                    "tmdbId": 1273002,
                    "title": "Avatar",
                    "originalTitle": "Avatar",
                    "year": 2009,
                    "monitored": True,
                    "hasFile": True,
                    "status": "released",
                    "movieFile": {
                        "id": 20,
                        "path": "/data/movies/Avatar (2009)/Avatar.mkv",
                        "relativePath": "Avatar.mkv",
                        "size": 1234,
                        "quality": {"quality": {"name": "Bluray-1080p"}},
                    },
                    "qualityProfile": {"name": "HD"},
                    "images": [
                        {"coverType": "poster", "remoteUrl": "https://image.test/avatar.jpg"}
                    ],
                }
            ],
        )

    with SessionLocal() as session:
        run = await LibrarySyncService(
            session,
            transports={integration.id: httpx.MockTransport(handler)},
        ).synchronize(integration_id=integration.id)

        assert run.items_total == 1
        assert run.files_total == 1
        movie = session.query(MediaItem).one()
        media_file = session.query(MediaFile).one()
        assert movie.media_type == MediaType.MOVIE
        assert movie.external_item_id == "10"
        assert movie.external_tmdb_id == "1273002"
        assert movie.title == "Avatar"
        assert movie.external_web_path == "/movie/1273002"
        assert media_file.quality == "Bluray-1080p"
        assert media_file.original_source_path.endswith("Avatar.mkv")


@pytest.mark.asyncio
async def test_sonarr_sync_links_multi_episode_file() -> None:
    reset_library()
    integration = add_integration(SourceType.SONARR)

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/series"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 7,
                        "title": "Demo Show",
                        "year": 2020,
                        "monitored": True,
                        "images": [
                            {"coverType": "poster", "remoteUrl": "https://image.test/show.jpg"}
                        ],
                    }
                ],
            )
        if request.url.path.endswith("/episodefile"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 99,
                        "path": "/data/tv/Demo Show/S01E01-E02.mkv",
                        "relativePath": "S01E01-E02.mkv",
                        "size": 4567,
                        "quality": {"quality": {"name": "WEBRip-1080p"}},
                        "episodeIds": [101, 102],
                    }
                ],
            )
        if request.url.path.endswith("/episode"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 101,
                        "title": "Part One",
                        "seasonNumber": 1,
                        "episodeNumber": 1,
                        "monitored": True,
                        "hasFile": True,
                        "episodeFileId": 99,
                    },
                    {
                        "id": 102,
                        "title": "Part Two",
                        "seasonNumber": 1,
                        "episodeNumber": 2,
                        "monitored": True,
                        "hasFile": True,
                        "episodeFileId": 99,
                    },
                ],
            )
        return httpx.Response(404)

    with SessionLocal() as session:
        run = await LibrarySyncService(
            session,
            transports={integration.id: httpx.MockTransport(handler)},
        ).synchronize(integration_id=integration.id)

        assert run.items_total == 2
        assert run.files_total == 1
        assert session.query(MediaItem).count() == 2
        assert session.query(MediaFile).count() == 1
        assert session.query(MediaItemFileLink).count() == 2


@pytest.mark.asyncio
async def test_sonarr_sync_links_episode_files_by_episode_ids() -> None:
    reset_library()
    integration = add_integration(SourceType.SONARR)

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/series"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 7,
                        "title": "Demo Show",
                        "year": 2020,
                        "monitored": True,
                    }
                ],
            )
        if request.url.path.endswith("/episodefile"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 99,
                        "path": "/data/tv/Demo Show/S01E01.mkv",
                        "relativePath": "S01E01.mkv",
                        "size": 4567,
                        "quality": {"quality": {"name": "WEBRip-1080p"}},
                        "episodeIds": [101],
                    }
                ],
            )
        if request.url.path.endswith("/episode"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 101,
                        "title": "Part One",
                        "seasonNumber": 1,
                        "episodeNumber": 1,
                        "monitored": True,
                        "hasFile": True,
                    },
                ],
            )
        return httpx.Response(404)

    with SessionLocal() as session:
        run = await LibrarySyncService(
            session,
            transports={integration.id: httpx.MockTransport(handler)},
        ).synchronize(integration_id=integration.id)

        assert run.items_total == 1
        assert run.files_total == 1
        episode = session.query(MediaItem).one()
        media_file = session.query(MediaFile).one()
        assert episode.file_presence is True
        assert media_file.quality == "WEBRip-1080p"
        assert session.query(MediaItemFileLink).count() == 1
