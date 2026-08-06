from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.audio import AudioStream
from app.models.enums import IgnoredObjectType, MediaType, ScanState, SourceType
from app.models.ignored import IgnoredItem
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.repositories.media import MediaRepository
from app.schemas.media import MediaFileSummary, MediaItemPage, MediaItemRead, SeriesSummary
from app.services.media_analysis import MediaAnalysisService

router = APIRouter(tags=["media"])

ITEM_SORT_FIELDS = {
    "title": MediaItem.title,
    "year": MediaItem.year,
    "season_number": MediaItem.season_number,
    "episode_number": MediaItem.episode_number,
    "updated_at": MediaItem.updated_at,
}


@router.get("/movies", response_model=MediaItemPage)
def list_movies(
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    integration_id: int | None = None,
    source_type: SourceType | None = None,
    search: str | None = None,
    monitored: bool | None = None,
    file_presence: bool | None = None,
    stale: bool | None = None,
    scan_state: ScanState | None = None,
    sort: str = "title",
    direction: str = "asc",
) -> MediaItemPage:
    return _list_items(
        session=session,
        media_type=MediaType.MOVIE,
        page=page,
        page_size=page_size,
        integration_id=integration_id,
        source_type=source_type,
        search=search,
        monitored=monitored,
        file_presence=file_presence,
        stale=stale,
        scan_state=scan_state,
        sort=sort,
        direction=direction,
    )


@router.get("/episodes", response_model=MediaItemPage)
def list_episodes(
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    integration_id: int | None = None,
    source_type: SourceType | None = None,
    search: str | None = None,
    monitored: bool | None = None,
    file_presence: bool | None = None,
    stale: bool | None = None,
    scan_state: ScanState | None = None,
    series: str | None = None,
    season: int | None = None,
    sort: str = "series_title",
    direction: str = "asc",
) -> MediaItemPage:
    return _list_items(
        session=session,
        media_type=MediaType.EPISODE,
        page=page,
        page_size=page_size,
        integration_id=integration_id,
        source_type=source_type,
        search=search,
        monitored=monitored,
        file_presence=file_presence,
        stale=stale,
        scan_state=scan_state,
        series=series,
        season=season,
        sort=sort,
        direction=direction,
    )


@router.get("/series", response_model=list[SeriesSummary])
def list_series(session: Session = Depends(get_session)) -> list[SeriesSummary]:
    statement = select(MediaItem).where(MediaItem.media_type == MediaType.EPISODE)
    episodes = list(session.scalars(statement))
    grouped: dict[tuple[int, str], list[MediaItem]] = {}
    for episode in episodes:
        if episode.external_series_id is None:
            continue
        grouped.setdefault((episode.integration_id, episode.external_series_id), []).append(episode)

    summaries: list[SeriesSummary] = []
    for (integration_id, external_series_id), grouped_episodes in grouped.items():
        files_scanned = 0
        missing = 0
        errors = 0
        for episode in grouped_episodes:
            first_file = _first_file(episode)
            if first_file is None:
                continue
            if first_file.last_scan_attempt is not None:
                files_scanned += 1
            if first_file.scan_state == ScanState.CZECH_AUDIO_MISSING:
                missing += 1
            if first_file.error_code:
                errors += 1
        first_episode = grouped_episodes[0]
        summaries.append(
            SeriesSummary(
                external_series_id=external_series_id,
                title=first_episode.series_title or first_episode.title,
                integration_id=integration_id,
                monitored=any(episode.monitored for episode in grouped_episodes),
                episode_count=len(grouped_episodes),
                files_scanned=files_scanned,
                episodes_missing_czech_audio=missing,
                errors=errors,
                poster_url=first_episode.poster_url,
                stale=all(episode.stale for episode in grouped_episodes),
            )
        )
    return sorted(summaries, key=lambda item: item.title.lower())


@router.get("/missing", response_model=MediaItemPage)
def list_missing_czech_audio(
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: str | None = None,
    include_ignored: bool = False,
) -> MediaItemPage:
    items = _missing_items(session, search=search, include_ignored=include_ignored)
    offset = (page - 1) * page_size
    return MediaItemPage(
        items=[_serialize_item(item) for item in items[offset : offset + page_size]],
        page=page,
        page_size=page_size,
        total=len(items),
    )


@router.get("/missing/export.csv")
def export_missing_czech_audio(
    session: Session = Depends(get_session),
    search: str | None = None,
    include_ignored: bool = False,
) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "media type",
            "movie title",
            "series title",
            "season",
            "episode",
            "episode title",
            "year",
            "quality",
            "detected languages",
            "scan state",
            "original path",
            "mapped path",
            "integration",
            "last scan",
        ]
    )
    for item in _missing_items(session, search=search, include_ignored=include_ignored):
        media_file = _first_file(item)
        languages = _audio_languages(session, media_file.id) if media_file else ""
        writer.writerow(
            [
                item.media_type,
                item.title if item.media_type == MediaType.MOVIE else "",
                item.series_title or "",
                item.season_number or "",
                item.episode_number or "",
                item.title if item.media_type == MediaType.EPISODE else "",
                item.year or "",
                media_file.quality if media_file else "",
                languages,
                media_file.scan_state if media_file else "",
                media_file.original_source_path if media_file else "",
                media_file.mapped_local_path if media_file else "",
                item.integration_id,
                media_file.last_scan_attempt if media_file else "",
            ]
        )
    csv_body = "\ufeff" + output.getvalue()
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="czecharr-missing-audio.csv"'},
    )


@router.post("/media-files/{media_file_id}/probe", response_model=MediaFileSummary)
async def probe_media_file(
    media_file_id: int,
    session: Session = Depends(get_session),
) -> MediaFile:
    try:
        outcome = await MediaAnalysisService(session).analyze_media_file(media_file_id, force=True)
        return outcome.media_file
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/media-files/{media_file_id}", response_model=MediaFileSummary)
def get_media_file(media_file_id: int, session: Session = Depends(get_session)) -> MediaFile:
    media_file = session.get(MediaFile, media_file_id)
    if media_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found.")
    return media_file


@router.get("/media-files/{media_file_id}/audio-streams")
def list_audio_streams(
    media_file_id: int, session: Session = Depends(get_session)
) -> list[dict[str, object]]:
    statement = (
        select(AudioStream)
        .where(AudioStream.media_file_id == media_file_id)
        .order_by(AudioStream.stream_index)
    )
    return [
        {
            "id": stream.id,
            "media_file_id": stream.media_file_id,
            "stream_index": stream.stream_index,
            "codec_name": stream.codec_name,
            "channels": stream.channels,
            "original_language": stream.original_language,
            "normalized_language": stream.normalized_language,
            "original_title": stream.original_title,
            "normalized_title": stream.normalized_title,
            "czech_match": stream.czech_match,
            "match_reason": stream.match_reason,
            "matched_value": stream.matched_value,
        }
        for stream in session.scalars(statement)
    ]


def _list_items(
    *,
    session: Session,
    media_type: MediaType,
    page: int,
    page_size: int,
    integration_id: int | None,
    source_type: SourceType | None,
    search: str | None,
    monitored: bool | None,
    file_presence: bool | None,
    stale: bool | None,
    scan_state: ScanState | None,
    sort: str,
    direction: str,
    series: str | None = None,
    season: int | None = None,
) -> MediaItemPage:
    statement: Select[tuple[MediaItem]] = select(MediaItem).where(
        MediaItem.media_type == media_type
    )
    if integration_id is not None:
        statement = statement.where(MediaItem.integration_id == integration_id)
    if source_type is not None:
        statement = statement.where(MediaItem.source_type == source_type)
    if monitored is not None:
        statement = statement.where(MediaItem.monitored.is_(monitored))
    if file_presence is not None:
        statement = statement.where(MediaItem.file_presence.is_(file_presence))
    if stale is not None:
        statement = statement.where(MediaItem.stale.is_(stale))
    if search:
        search_pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                MediaItem.title.ilike(search_pattern),
                MediaItem.original_title.ilike(search_pattern),
                MediaItem.series_title.ilike(search_pattern),
            )
        )
    if series:
        statement = statement.where(MediaItem.external_series_id == series)
    if season is not None:
        statement = statement.where(MediaItem.season_number == season)
    if scan_state is not None:
        statement = (
            statement.join(MediaItemFileLink, MediaItemFileLink.media_item_id == MediaItem.id)
            .join(MediaFile, MediaFile.id == MediaItemFileLink.media_file_id)
            .where(MediaFile.scan_state == scan_state)
        )

    sort_column = ITEM_SORT_FIELDS.get(sort)
    if sort == "series_title":
        sort_column = MediaItem.series_title
    if sort_column is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported sort field: {sort}",
        )
    if direction not in {"asc", "desc"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported sort direction.",
        )
    ordered_column = sort_column.desc() if direction == "desc" else sort_column.asc()
    statement = statement.order_by(ordered_column, MediaItem.id.asc())

    items, total = MediaRepository(session).paged_items(statement, page=page, page_size=page_size)
    return MediaItemPage(
        items=[_serialize_item(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


def _serialize_item(item: MediaItem) -> MediaItemRead:
    media_file = _first_file(item)
    return MediaItemRead.model_validate(
        {
            **item.__dict__,
            "media_file": (
                MediaFileSummary.model_validate(media_file, from_attributes=True)
                if media_file
                else None
            ),
        }
    )


def _first_file(item: MediaItem) -> MediaFile | None:
    if not item.file_links:
        return None
    return item.file_links[0].media_file


def _missing_items(
    session: Session,
    *,
    search: str | None,
    include_ignored: bool,
) -> list[MediaItem]:
    ignored_item_ids = set()
    ignored_file_ids = set()
    if not include_ignored:
        ignored_item_ids = {
            item.object_id
            for item in session.scalars(
                select(IgnoredItem).where(IgnoredItem.object_type == IgnoredObjectType.MEDIA_ITEM)
            )
        }
        ignored_file_ids = {
            item.object_id
            for item in session.scalars(
                select(IgnoredItem).where(IgnoredItem.object_type == IgnoredObjectType.MEDIA_FILE)
            )
        }
    statement = select(MediaItem).where(MediaItem.stale.is_(False)).order_by(MediaItem.title)
    items = list(session.scalars(statement))
    normalized_search = search.casefold().strip() if search else None
    result: list[MediaItem] = []
    for item in items:
        media_file = _first_file(item)
        if media_file is None or media_file.scan_state != ScanState.CZECH_AUDIO_MISSING:
            continue
        if item.id in ignored_item_ids or media_file.id in ignored_file_ids:
            continue
        if normalized_search:
            haystack = " ".join(
                value or ""
                for value in [
                    item.title,
                    item.original_title,
                    item.series_title,
                    media_file.quality,
                ]
            ).casefold()
            if normalized_search not in haystack:
                continue
        result.append(item)
    return result


def _audio_languages(session: Session, media_file_id: int) -> str:
    statement = select(AudioStream.normalized_language).where(
        AudioStream.media_file_id == media_file_id
    )
    return ", ".join(sorted({language for language in session.scalars(statement) if language}))
