from __future__ import annotations

import csv
import io
import re
import shlex
import unicodedata
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_session
from app.models.audio import AudioStream
from app.models.enums import IgnoredObjectType, MediaType, ScanState, SourceType
from app.models.ignored import IgnoredItem
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.repositories.media import MediaRepository
from app.schemas.media import (
    AudioStreamRead,
    FfmpegRepairPlan,
    FfmpegRepairPlanRequest,
    MediaFileSummary,
    MediaItemPage,
    MediaItemRead,
    SeasonSummary,
    SeriesSummary,
)
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
    title_expression = func.coalesce(func.max(MediaItem.series_title), func.max(MediaItem.title))
    statement = (
        select(
            MediaItem.integration_id.label("integration_id"),
            MediaItem.external_series_id.label("external_series_id"),
            title_expression.label("title"),
            func.max(case((MediaItem.monitored.is_(True), 1), else_=0)).label("monitored"),
            func.count(func.distinct(MediaItem.id)).label("episode_count"),
            func.count(
                func.distinct(
                    case((MediaFile.last_scan_attempt.is_not(None), MediaFile.id), else_=None)
                )
            ).label("files_scanned"),
            func.count(
                func.distinct(
                    case(
                        (
                            MediaFile.scan_state == ScanState.CZECH_AUDIO_MISSING,
                            MediaItem.id,
                        ),
                        else_=None,
                    )
                )
            ).label("episodes_missing_czech_audio"),
            func.count(
                func.distinct(case((MediaFile.error_code.is_not(None), MediaItem.id), else_=None))
            ).label("errors"),
            func.max(MediaItem.poster_url).label("poster_url"),
            func.min(case((MediaItem.stale.is_(True), 1), else_=0)).label("stale"),
            func.max(MediaItem.external_web_path).label("external_web_path"),
            Integration.base_url.label("base_url"),
            Integration.web_url.label("web_url"),
        )
        .join(Integration, Integration.id == MediaItem.integration_id)
        .outerjoin(MediaItemFileLink, MediaItemFileLink.media_item_id == MediaItem.id)
        .outerjoin(MediaFile, MediaFile.id == MediaItemFileLink.media_file_id)
        .where(MediaItem.media_type == MediaType.EPISODE)
        .where(MediaItem.external_series_id.is_not(None))
        .group_by(
            MediaItem.integration_id,
            MediaItem.external_series_id,
            Integration.base_url,
            Integration.web_url,
        )
        .order_by(func.lower(title_expression))
    )

    return [
        SeriesSummary(
            external_series_id=str(row.external_series_id),
            title=str(row.title or "Untitled series"),
            integration_id=int(row.integration_id),
            monitored=bool(row.monitored),
            episode_count=int(row.episode_count or 0),
            files_scanned=int(row.files_scanned or 0),
            episodes_missing_czech_audio=int(row.episodes_missing_czech_audio or 0),
            errors=int(row.errors or 0),
            poster_url=row.poster_url,
            stale=bool(row.stale),
            source_web_url=_source_web_url(
                row.web_url or row.base_url,
                row.external_web_path or _derived_series_web_path(str(row.title or "")),
            ),
        )
        for row in session.execute(statement)
    ]


@router.get(
    "/series/{integration_id}/{external_series_id}/seasons", response_model=list[SeasonSummary]
)
def list_series_seasons(
    integration_id: int,
    external_series_id: str,
    session: Session = Depends(get_session),
) -> list[SeasonSummary]:
    statement = (
        select(
            MediaItem.integration_id.label("integration_id"),
            MediaItem.external_series_id.label("external_series_id"),
            MediaItem.season_number.label("season_number"),
            func.count(func.distinct(MediaItem.id)).label("episode_count"),
            func.count(
                func.distinct(
                    case((MediaFile.last_scan_attempt.is_not(None), MediaFile.id), else_=None)
                )
            ).label("files_scanned"),
            func.count(
                func.distinct(
                    case(
                        (
                            MediaFile.scan_state == ScanState.CZECH_AUDIO_MISSING,
                            MediaItem.id,
                        ),
                        else_=None,
                    )
                )
            ).label("episodes_missing_czech_audio"),
            func.count(
                func.distinct(case((MediaFile.error_code.is_not(None), MediaItem.id), else_=None))
            ).label("errors"),
            func.min(case((MediaItem.stale.is_(True), 1), else_=0)).label("stale"),
        )
        .outerjoin(MediaItemFileLink, MediaItemFileLink.media_item_id == MediaItem.id)
        .outerjoin(MediaFile, MediaFile.id == MediaItemFileLink.media_file_id)
        .where(MediaItem.media_type == MediaType.EPISODE)
        .where(MediaItem.integration_id == integration_id)
        .where(MediaItem.external_series_id == external_series_id)
        .group_by(MediaItem.integration_id, MediaItem.external_series_id, MediaItem.season_number)
        .order_by(MediaItem.season_number)
    )

    return [
        SeasonSummary(
            integration_id=int(row.integration_id),
            external_series_id=str(row.external_series_id),
            season_number=row.season_number,
            episode_count=int(row.episode_count or 0),
            files_scanned=int(row.files_scanned or 0),
            episodes_missing_czech_audio=int(row.episodes_missing_czech_audio or 0),
            errors=int(row.errors or 0),
            stale=bool(row.stale),
        )
        for row in session.execute(statement)
    ]


@router.get("/missing", response_model=MediaItemPage)
def list_missing_czech_audio(
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: str | None = None,
    include_ignored: bool = False,
) -> MediaItemPage:
    items, total = _missing_items(
        session,
        search=search,
        include_ignored=include_ignored,
        page=page,
        page_size=page_size,
    )
    return MediaItemPage(
        items=_serialize_items(session, items),
        page=page,
        page_size=page_size,
        total=total,
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
    items, _ = _missing_items(
        session,
        search=search,
        include_ignored=include_ignored,
        page=None,
        page_size=None,
    )
    for item in items:
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


@router.get("/media-files/{media_file_id}/audio-streams", response_model=list[AudioStreamRead])
def list_audio_streams(
    media_file_id: int, session: Session = Depends(get_session)
) -> list[AudioStreamRead]:
    statement = (
        select(AudioStream)
        .where(AudioStream.media_file_id == media_file_id)
        .order_by(AudioStream.stream_index)
    )
    return [AudioStreamRead.model_validate(stream) for stream in session.scalars(statement)]


@router.post(
    "/media-files/{media_file_id}/ffmpeg-repair-plan",
    response_model=FfmpegRepairPlan,
)
def create_ffmpeg_repair_plan(
    media_file_id: int,
    payload: FfmpegRepairPlanRequest,
    session: Session = Depends(get_session),
) -> FfmpegRepairPlan:
    media_file = session.get(MediaFile, media_file_id)
    if media_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found.")
    stream = session.get(AudioStream, payload.audio_stream_id)
    if stream is None or stream.media_file_id != media_file_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio stream not found.")
    if not media_file.mapped_local_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Media file does not have a mapped local path.",
        )

    streams = list(
        session.scalars(
            select(AudioStream)
            .where(AudioStream.media_file_id == media_file_id)
            .order_by(AudioStream.stream_index)
        )
    )
    audio_ordinal = next(
        index for index, candidate in enumerate(streams) if candidate.id == stream.id
    )
    output_path = _repair_output_path(media_file)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        media_file.mapped_local_path,
        "-map",
        "0",
        "-c",
        "copy",
        f"-metadata:s:a:{audio_ordinal}",
        f"language={payload.language_code}",
        f"-metadata:s:a:{audio_ordinal}",
        f"title={payload.title}",
        output_path,
    ]
    return FfmpegRepairPlan(
        media_file_id=media_file.id,
        audio_stream_id=stream.id,
        audio_stream_index=stream.stream_index,
        audio_stream_ordinal=audio_ordinal,
        input_path=media_file.mapped_local_path,
        output_path=output_path,
        command=command,
        display_command=shlex.join(command),
        warning=(
            "This command is a manual repair plan. Czecharr does not execute it and does not "
            "modify media files. It writes a remuxed copy under the configured /config repair "
            "directory when run inside the container."
        ),
    )


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
        items=_serialize_items(session, items),
        page=page,
        page_size=page_size,
        total=total,
    )


def _serialize_items(session: Session, items: list[MediaItem]) -> list[MediaItemRead]:
    integrations = _integration_map(session, items)
    return [_serialize_item(item, integrations.get(item.integration_id)) for item in items]


def _serialize_item(item: MediaItem, integration: Integration | None) -> MediaItemRead:
    media_file = _first_file(item)
    external_web_path = _item_external_web_path(item)
    return MediaItemRead.model_validate(
        {
            **item.__dict__,
            "source_web_url": _source_web_url(
                integration.web_url or integration.base_url if integration else None,
                external_web_path,
            ),
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
    page: int | None,
    page_size: int | None,
) -> tuple[list[MediaItem], int]:
    id_statement = _missing_item_ids_statement(
        search=search,
        include_ignored=include_ignored,
    )
    total = (
        session.scalar(select(func.count()).select_from(id_statement.order_by(None).subquery()))
        or 0
    )
    if page is not None and page_size is not None:
        id_statement = id_statement.offset((page - 1) * page_size).limit(page_size)

    item_ids = list(session.scalars(id_statement))
    if not item_ids:
        return [], int(total)

    items_statement = (
        select(MediaItem)
        .where(MediaItem.id.in_(item_ids))
        .options(selectinload(MediaItem.file_links).selectinload(MediaItemFileLink.media_file))
    )
    items_by_id = {item.id: item for item in session.scalars(items_statement)}
    return [items_by_id[item_id] for item_id in item_ids if item_id in items_by_id], int(total)


def _missing_item_ids_statement(
    *,
    search: str | None,
    include_ignored: bool,
) -> Select[tuple[int]]:
    statement: Select[tuple[int]] = (
        select(MediaItem.id)
        .join(MediaItemFileLink, MediaItemFileLink.media_item_id == MediaItem.id)
        .join(MediaFile, MediaFile.id == MediaItemFileLink.media_file_id)
        .where(MediaItem.stale.is_(False))
        .where(MediaFile.stale.is_(False))
        .where(MediaFile.scan_state == ScanState.CZECH_AUDIO_MISSING)
        .group_by(MediaItem.id)
        .order_by(
            func.lower(func.coalesce(MediaItem.series_title, MediaItem.title)),
            MediaItem.season_number,
            MediaItem.episode_number,
            MediaItem.id,
        )
    )
    if not include_ignored:
        ignored_item_ids = select(IgnoredItem.object_id).where(
            IgnoredItem.object_type == IgnoredObjectType.MEDIA_ITEM
        )
        ignored_file_ids = select(IgnoredItem.object_id).where(
            IgnoredItem.object_type == IgnoredObjectType.MEDIA_FILE
        )
        statement = statement.where(MediaItem.id.not_in(ignored_item_ids)).where(
            MediaFile.id.not_in(ignored_file_ids)
        )
    if search:
        search_pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                MediaItem.title.ilike(search_pattern),
                MediaItem.original_title.ilike(search_pattern),
                MediaItem.series_title.ilike(search_pattern),
                MediaFile.quality.ilike(search_pattern),
            )
        )
    return statement


def _integration_map(session: Session, items: list[MediaItem]) -> dict[int, Integration]:
    integration_ids = {item.integration_id for item in items}
    if not integration_ids:
        return {}
    statement = select(Integration).where(Integration.id.in_(integration_ids))
    return {integration.id: integration for integration in session.scalars(statement)}


def _item_external_web_path(item: MediaItem) -> str | None:
    if item.media_type == MediaType.MOVIE and item.source_type == SourceType.RADARR:
        if item.external_web_path and _is_numeric_movie_web_path(item.external_web_path):
            return item.external_web_path
        return _derived_item_web_path(item)
    return item.external_web_path or _derived_item_web_path(item)


def _is_numeric_movie_web_path(value: str) -> bool:
    return re.fullmatch(r"/?movie/\d+/?", value.strip()) is not None


def _source_web_url(base_url: str | None, external_web_path: str | None) -> str | None:
    if not base_url or not external_web_path:
        return None
    return f"{base_url.rstrip('/')}/{external_web_path.lstrip('/')}"


def _derived_item_web_path(item: MediaItem) -> str | None:
    if item.media_type == MediaType.MOVIE:
        return _web_path("movie", item.external_item_id)
    if item.external_series_id or item.series_title:
        return _derived_series_web_path(item.series_title or item.title)
    return None


def _derived_series_web_path(title: str) -> str | None:
    return _derived_web_path("series", title)


def _derived_web_path(section: str, title: str) -> str | None:
    slug = _slugify(title)
    return f"/{section}/{slug}" if slug else None


def _web_path(section: str, value: object) -> str | None:
    text = str(value).strip()
    if not text:
        return None
    return f"/{section}/{quote(text, safe='')}"


def _slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return "-".join(re.findall(r"[a-z0-9]+", ascii_value.lower()))


def _repair_output_path(media_file: MediaFile) -> str:
    config_dir = get_settings().config_dir
    filename = Path(media_file.mapped_local_path or "").name or f"media-file-{media_file.id}.mkv"
    source_filename = Path(filename)
    suffix = source_filename.suffix or ".mkv"
    stem = source_filename.stem or f"media-file-{media_file.id}"
    return (config_dir / "repair" / f"{stem}.czecharr-fixed{suffix}").as_posix()


def _audio_languages(session: Session, media_file_id: int) -> str:
    statement = select(AudioStream.normalized_language).where(
        AudioStream.media_file_id == media_file_id
    )
    return ", ".join(sorted({language for language in session.scalars(statement) if language}))
