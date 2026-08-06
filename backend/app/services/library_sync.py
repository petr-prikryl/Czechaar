from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.integrations.arr_client import ArrApiError, RadarrClient, SonarrClient
from app.models.enums import MediaType, SourceType, SyncStatus
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem
from app.models.sync import LibrarySyncRun
from app.repositories.integrations import IntegrationRepository
from app.repositories.media import MediaRepository


class LibrarySyncService:
    def __init__(
        self,
        session: Session,
        transports: dict[int, httpx.AsyncBaseTransport] | None = None,
    ) -> None:
        self.session = session
        self.transports = transports or {}
        self.media_repository = MediaRepository(session)

    async def synchronize(
        self,
        *,
        source_type: SourceType | None = None,
        integration_id: int | None = None,
    ) -> LibrarySyncRun:
        run = LibrarySyncRun(
            source_type=source_type,
            integration_id=integration_id,
            status=SyncStatus.RUNNING,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        try:
            integrations = self._select_integrations(
                source_type=source_type, integration_id=integration_id
            )
            for integration in integrations:
                if SourceType(integration.source_type) == SourceType.RADARR:
                    item_count, file_count, stale_count = await self._sync_radarr(integration)
                else:
                    item_count, file_count, stale_count = await self._sync_sonarr(integration)
                run.items_total += item_count
                run.files_total += file_count
                run.stale_count += stale_count
            run.status = SyncStatus.COMPLETED
        except (ArrApiError, httpx.HTTPError, ValueError) as exc:
            run.status = SyncStatus.FAILED
            run.error_message = str(exc)
        finally:
            run.finished_at = datetime.now(UTC)
            self.session.add(run)
            self.session.commit()
            self.session.refresh(run)

        return run

    def _select_integrations(
        self,
        *,
        source_type: SourceType | None,
        integration_id: int | None,
    ) -> list[Integration]:
        if integration_id is not None:
            integration = IntegrationRepository(self.session).get(integration_id)
            if integration is None:
                raise ValueError("Integration not found.")
            return [integration]

        statement = select(Integration).where(Integration.enabled.is_(True))
        if source_type is not None:
            statement = statement.where(Integration.source_type == source_type)
        return list(self.session.scalars(statement.order_by(Integration.id)))

    async def _sync_radarr(self, integration: Integration) -> tuple[int, int, int]:
        client = RadarrClient(
            base_url=integration.base_url,
            api_key=integration.api_key,
            api_key_env_var=integration.api_key_env_var,
            timeout_seconds=integration.timeout_seconds,
            verify_tls=integration.verify_tls,
            transport=self.transports.get(integration.id),
        )
        movies = await client.list_movies()
        seen_items: set[str] = set()
        seen_files: set[str] = set()
        for movie in movies:
            item = self._upsert_radarr_movie(integration, movie)
            seen_items.add(item.external_item_id)

            movie_file = _as_dict(movie.get("movieFile"))
            if movie_file:
                media_file = self._upsert_radarr_file(integration, movie, movie_file)
                seen_files.add(media_file.external_file_id)
                self.media_repository.ensure_link(item, media_file)

        stale_count = self._mark_stale(integration, seen_items, seen_files)
        self.session.commit()
        return len(seen_items), len(seen_files), stale_count

    async def _sync_sonarr(self, integration: Integration) -> tuple[int, int, int]:
        client = SonarrClient(
            base_url=integration.base_url,
            api_key=integration.api_key,
            api_key_env_var=integration.api_key_env_var,
            timeout_seconds=integration.timeout_seconds,
            verify_tls=integration.verify_tls,
            transport=self.transports.get(integration.id),
        )
        seen_items: set[str] = set()
        seen_files: set[str] = set()
        for series in await client.list_series():
            series_id = int(series["id"])
            file_payloads = await client.list_episode_files(series_id)
            files_by_id = {
                str(file_payload.get("id")): file_payload for file_payload in file_payloads
            }
            for episode in await client.list_episodes(series_id):
                item = self._upsert_sonarr_episode(integration, series, episode)
                seen_items.add(item.external_item_id)
                episode_file_id = episode.get("episodeFileId")
                if episode_file_id is None:
                    continue
                file_payload = _as_dict(episode.get("episodeFile")) or files_by_id.get(
                    str(episode_file_id)
                )
                if not file_payload:
                    continue
                media_file = self._upsert_sonarr_file(integration, file_payload)
                seen_files.add(media_file.external_file_id)
                self.media_repository.ensure_link(item, media_file)

        stale_count = self._mark_stale(integration, seen_items, seen_files)
        self.session.commit()
        return len(seen_items), len(seen_files), stale_count

    def _upsert_radarr_movie(self, integration: Integration, movie: dict[str, Any]) -> MediaItem:
        external_id = str(movie["id"])
        item = self.media_repository.get_item(
            integration_id=integration.id,
            media_type=MediaType.MOVIE,
            external_item_id=external_id,
        ) or MediaItem(
            integration_id=integration.id,
            source_type=SourceType.RADARR,
            media_type=MediaType.MOVIE,
            external_item_id=external_id,
        )
        item.title = str(movie.get("title") or movie.get("originalTitle") or "Untitled movie")
        item.original_title = _optional_str(movie.get("originalTitle"))
        item.external_web_path = _radarr_movie_web_path(movie)
        item.year = _optional_int(movie.get("year"))
        item.monitored = bool(movie.get("monitored", True))
        item.file_presence = bool(movie.get("hasFile") or movie.get("movieFile"))
        item.upstream_status = _optional_str(movie.get("status"))
        item.poster_url = _poster_url(movie.get("images"))
        item.stale = False
        self.session.add(item)
        return item

    def _upsert_radarr_file(
        self,
        integration: Integration,
        movie: dict[str, Any],
        movie_file: dict[str, Any],
    ) -> MediaFile:
        external_file_id = str(movie_file["id"])
        media_file = self.media_repository.get_file(
            integration_id=integration.id,
            external_file_id=external_file_id,
        ) or MediaFile(
            integration_id=integration.id,
            source_type=SourceType.RADARR,
            external_file_id=external_file_id,
            original_source_path="",
        )
        media_file.original_source_path = str(movie_file.get("path") or "")
        media_file.relative_path = _optional_str(movie_file.get("relativePath"))
        media_file.size = _optional_int(movie_file.get("size"))
        media_file.quality = _quality_name(movie_file.get("quality"))
        media_file.quality_profile = _quality_profile_name(movie)
        media_file.stale = False
        self.session.add(media_file)
        return media_file

    def _upsert_sonarr_episode(
        self,
        integration: Integration,
        series: dict[str, Any],
        episode: dict[str, Any],
    ) -> MediaItem:
        external_id = str(episode["id"])
        item = self.media_repository.get_item(
            integration_id=integration.id,
            media_type=MediaType.EPISODE,
            external_item_id=external_id,
        ) or MediaItem(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            media_type=MediaType.EPISODE,
            external_item_id=external_id,
        )
        item.external_series_id = str(series["id"])
        item.external_web_path = _web_path("series", series.get("titleSlug"))
        item.title = str(episode.get("title") or "Untitled episode")
        item.series_title = str(series.get("title") or "Untitled series")
        item.year = _optional_int(series.get("year"))
        item.season_number = _optional_int(episode.get("seasonNumber"))
        item.episode_number = _optional_int(episode.get("episodeNumber"))
        item.absolute_episode_number = _optional_int(episode.get("absoluteEpisodeNumber"))
        item.monitored = bool(episode.get("monitored", True)) and bool(
            series.get("monitored", True)
        )
        item.file_presence = bool(episode.get("hasFile") or episode.get("episodeFileId"))
        item.upstream_status = _optional_str(episode.get("airDateUtc") or episode.get("airDate"))
        item.poster_url = _poster_url(series.get("images"))
        item.stale = False
        self.session.add(item)
        return item

    def _upsert_sonarr_file(
        self, integration: Integration, file_payload: dict[str, Any]
    ) -> MediaFile:
        external_file_id = str(file_payload["id"])
        media_file = self.media_repository.get_file(
            integration_id=integration.id,
            external_file_id=external_file_id,
        ) or MediaFile(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            external_file_id=external_file_id,
            original_source_path="",
        )
        media_file.original_source_path = str(file_payload.get("path") or "")
        media_file.relative_path = _optional_str(file_payload.get("relativePath"))
        media_file.size = _optional_int(file_payload.get("size"))
        media_file.quality = _quality_name(file_payload.get("quality"))
        media_file.stale = False
        self.session.add(media_file)
        return media_file

    def _mark_stale(
        self,
        integration: Integration,
        seen_items: set[str],
        seen_files: set[str],
    ) -> int:
        item_statement = (
            update(MediaItem)
            .where(MediaItem.integration_id == integration.id)
            .where(MediaItem.external_item_id.not_in(seen_items))
            .values(stale=True)
        )
        file_statement = (
            update(MediaFile)
            .where(MediaFile.integration_id == integration.id)
            .where(MediaFile.external_file_id.not_in(seen_files))
            .values(stale=True)
        )
        item_result = self.session.execute(item_statement)
        file_result = self.session.execute(file_statement)
        item_rowcount = getattr(item_result, "rowcount", 0)
        file_rowcount = getattr(file_result, "rowcount", 0)
        return int(item_rowcount or 0) + int(file_rowcount or 0)


def _as_dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _quality_name(value: Any) -> str | None:
    quality = _as_dict(value)
    if not quality:
        return None
    nested_quality = _as_dict(quality.get("quality"))
    if nested_quality and nested_quality.get("name"):
        return str(nested_quality["name"])
    if quality.get("name"):
        return str(quality["name"])
    return None


def _quality_profile_name(value: dict[str, Any]) -> str | None:
    profile = _as_dict(value.get("qualityProfile"))
    if profile and profile.get("name"):
        return str(profile["name"])
    return None


def _poster_url(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    for image in value:
        image_payload = _as_dict(image)
        if not image_payload:
            continue
        cover_type = str(image_payload.get("coverType") or "")
        if cover_type in {"poster", "banner"}:
            return _optional_str(image_payload.get("remoteUrl") or image_payload.get("url"))
    return None


def _web_path(section: str, slug_value: Any) -> str | None:
    slug = _optional_str(slug_value)
    if slug is None:
        return None
    return f"/{section}/{quote(slug, safe='')}"


def _radarr_movie_web_path(movie: dict[str, Any]) -> str | None:
    return _web_path("movie", movie.get("tmdbId") or movie.get("id"))
