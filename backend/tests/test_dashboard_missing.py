from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.api.v1.media as media_api
from app.db.session import SessionLocal, initialize_database
from app.main import create_app
from app.models.audio import AudioStream
from app.models.enums import IgnoredObjectType, MediaType, ScanState, SourceType
from app.models.ignored import IgnoredItem
from app.models.integration import Integration
from app.models.media import MediaFile, MediaItem, MediaItemFileLink
from app.models.path_mapping import AllowedMediaRoot


def reset_dashboard_data() -> tuple[int, int]:
    initialize_database()
    with SessionLocal() as session:
        session.query(IgnoredItem).delete()
        session.query(AudioStream).delete()
        session.query(MediaItemFileLink).delete()
        session.query(MediaFile).delete()
        session.query(MediaItem).delete()
        session.query(Integration).delete()
        integration = Integration(
            source_type=SourceType.RADARR,
            name="Radarr",
            base_url="https://radarr.test",
            web_url="https://radarr-web.test",
            api_key="key",
            enabled=True,
            timeout_seconds=10,
            verify_tls=True,
        )
        session.add(integration)
        session.flush()
        item = MediaItem(
            integration_id=integration.id,
            source_type=SourceType.RADARR,
            external_item_id="163",
            external_tmdb_id="1273002",
            external_web_path="/movie/1273002",
            media_type=MediaType.MOVIE,
            title="Missing Movie",
            monitored=True,
            file_presence=True,
        )
        media_file = MediaFile(
            integration_id=integration.id,
            source_type=SourceType.RADARR,
            external_file_id="2",
            original_source_path="/data/movie.mkv",
            mapped_local_path="/movies/Missing Movie.mkv",
            scan_state=ScanState.CZECH_AUDIO_MISSING,
            quality="Bluray-1080p",
        )
        session.add_all([item, media_file])
        session.flush()
        session.add(MediaItemFileLink(media_item_id=item.id, media_file_id=media_file.id))
        session.commit()
        return item.id, media_file.id


def test_dashboard_stats_include_missing_audio() -> None:
    reset_dashboard_data()
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_movies"] == 1
    assert payload["files_missing_czech_audio"] == 1


def test_missing_audio_respects_ignored_filter() -> None:
    item_id, _ = reset_dashboard_data()
    with SessionLocal() as session:
        session.add(IgnoredItem(object_type=IgnoredObjectType.MEDIA_ITEM, object_id=item_id))
        session.commit()

    with TestClient(create_app()) as client:
        hidden = client.get("/api/v1/missing")
        visible = client.get("/api/v1/missing?include_ignored=true")

    assert hidden.json()["total"] == 0
    assert visible.json()["total"] == 1


def test_missing_audio_is_paginated_and_includes_source_web_url() -> None:
    reset_dashboard_data()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing?page=1&page_size=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["source_web_url"] == "https://radarr-web.test/movie/1273002"


def test_missing_audio_derives_radarr_url_from_tmdb_id_when_web_path_is_missing() -> None:
    item_id, _ = reset_dashboard_data()
    with SessionLocal() as session:
        item = session.get(MediaItem, item_id)
        assert item is not None
        item.external_web_path = None
        item.year = 2024
        session.add(item)
        session.commit()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing?page=1&page_size=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["source_web_url"] == "https://radarr-web.test/movie/1273002"


def test_missing_audio_ignores_legacy_radarr_internal_id_web_path() -> None:
    item_id, _ = reset_dashboard_data()
    with SessionLocal() as session:
        item = session.get(MediaItem, item_id)
        assert item is not None
        item.external_web_path = "/movie/163"
        session.add(item)
        session.commit()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing?page=1&page_size=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["source_web_url"] == "https://radarr-web.test/movie/1273002"


def test_missing_audio_ignores_legacy_radarr_title_slug_web_path() -> None:
    item_id, _ = reset_dashboard_data()
    with SessionLocal() as session:
        item = session.get(MediaItem, item_id)
        assert item is not None
        item.external_web_path = "/movie/missing-movie-2024"
        session.add(item)
        session.commit()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing?page=1&page_size=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["source_web_url"] == "https://radarr-web.test/movie/1273002"


def test_missing_audio_does_not_fall_back_to_radarr_internal_movie_id() -> None:
    item_id, _ = reset_dashboard_data()
    with SessionLocal() as session:
        item = session.get(MediaItem, item_id)
        assert item is not None
        item.external_tmdb_id = None
        item.external_web_path = "/movie/163"
        session.add(item)
        session.commit()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing?page=1&page_size=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["source_web_url"] is None


def test_ffmpeg_repair_plan_is_generated_without_executing_ffmpeg() -> None:
    _, media_file_id = reset_dashboard_data()
    with SessionLocal() as session:
        stream = AudioStream(
            media_file_id=media_file_id,
            stream_index=2,
            codec_name="aac",
            original_language=None,
            normalized_language=None,
            original_title=None,
            normalized_title=None,
            czech_match=False,
            match_reason="no_match",
        )
        session.add(stream)
        session.commit()
        stream_id = stream.id

    with TestClient(create_app()) as client:
        response = client.post(
            f"/api/v1/media-files/{media_file_id}/ffmpeg-repair-plan",
            json={
                "audio_stream_id": stream_id,
                "language_code": "cze",
                "title": "Čeština",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["command"][0] == "ffmpeg"
    assert payload["input_path"] == "/movies/Missing Movie.mkv"
    assert payload["output_path"].endswith("Missing Movie.czecharr-fixed.mkv")
    assert "language=cze" in payload["command"]
    assert "title=Čeština" in payload["command"]
    assert "does not execute" in payload["warning"]


def test_czech_metadata_update_is_disabled_by_default(monkeypatch) -> None:
    _, media_file_id = reset_dashboard_data()
    with SessionLocal() as session:
        stream = AudioStream(
            media_file_id=media_file_id,
            stream_index=2,
            codec_name="aac",
            czech_match=False,
            match_reason="no_match",
        )
        session.add(stream)
        session.commit()
        stream_id = stream.id

    monkeypatch.setattr(
        media_api,
        "get_settings",
        lambda: SimpleNamespace(metadata_edit_enabled=False, mkvpropedit_path="mkvpropedit"),
    )

    with TestClient(create_app()) as client:
        response = client.post(
            f"/api/v1/media-files/{media_file_id}/audio-streams/czech-metadata",
            json={"audio_stream_id": stream_id},
        )

    assert response.status_code == 403


def test_czech_metadata_update_runs_mkvpropedit_and_marks_stream(
    tmp_path: Path,
    monkeypatch,
) -> None:
    media_path = tmp_path / "movie.mkv"
    media_path.write_bytes(b"matroska")
    _, media_file_id = reset_dashboard_data()
    with SessionLocal() as session:
        media_file = session.get(MediaFile, media_file_id)
        assert media_file is not None
        media_file.mapped_local_path = str(media_path)
        stream = AudioStream(
            media_file_id=media_file_id,
            stream_index=2,
            codec_name="aac",
            original_language="und",
            normalized_language="und",
            czech_match=False,
            match_reason="no_match",
        )
        session.add_all(
            [
                media_file,
                stream,
                AllowedMediaRoot(path=str(tmp_path), enabled=True),
            ]
        )
        session.commit()
        stream_id = stream.id

    captured: dict[str, list[str]] = {}

    async def fake_run_mkvpropedit(command: list[str]) -> None:
        captured["command"] = command

    monkeypatch.setattr(
        media_api,
        "get_settings",
        lambda: SimpleNamespace(metadata_edit_enabled=True, mkvpropedit_path="mkvpropedit"),
    )
    monkeypatch.setattr(media_api, "_run_mkvpropedit", fake_run_mkvpropedit)

    with TestClient(create_app()) as client:
        response = client.post(
            f"/api/v1/media-files/{media_file_id}/audio-streams/czech-metadata",
            json={"audio_stream_id": stream_id},
        )

    assert response.status_code == 200
    assert captured["command"] == [
        "mkvpropedit",
        str(media_path),
        "--edit",
        "track:a1",
        "--set",
        "language=ces",
        "--set",
        "name=\u010ce\u0161tina",
    ]
    payload = response.json()
    assert payload["scan_state"] == "czech_audio_found"
    assert payload["czech_audio_result"] is True

    with SessionLocal() as session:
        stream = session.get(AudioStream, stream_id)
        assert stream is not None
        assert stream.original_language == "ces"
        assert stream.original_title == "\u010ce\u0161tina"
        assert stream.czech_match is True


def test_missing_csv_uses_utf8_bom() -> None:
    reset_dashboard_data()
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing/export.csv")

    assert response.status_code == 200
    assert response.content.startswith("\ufeff".encode("utf-8"))
    assert "Missing Movie" in response.text


def test_series_and_seasons_are_aggregated() -> None:
    initialize_database()
    with SessionLocal() as session:
        session.query(IgnoredItem).delete()
        session.query(AudioStream).delete()
        session.query(MediaItemFileLink).delete()
        session.query(MediaFile).delete()
        session.query(MediaItem).delete()
        session.query(Integration).delete()
        integration = Integration(
            source_type=SourceType.SONARR,
            name="Sonarr",
            base_url="https://sonarr-api.test",
            web_url="https://sonarr.test",
            api_key="key",
            enabled=True,
            timeout_seconds=10,
            verify_tls=True,
        )
        session.add(integration)
        session.flush()
        file_one = MediaFile(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            external_file_id="99",
            original_source_path="/data/tv/demo/s01e01.mkv",
            scan_state=ScanState.CZECH_AUDIO_MISSING,
            last_scan_attempt=datetime(2026, 8, 6, 10, 0, tzinfo=UTC),
        )
        file_two = MediaFile(
            integration_id=integration.id,
            source_type=SourceType.SONARR,
            external_file_id="100",
            original_source_path="/data/tv/demo/s02e01.mkv",
            scan_state=ScanState.CZECH_AUDIO_FOUND,
            last_scan_attempt=datetime(2026, 8, 6, 10, 1, tzinfo=UTC),
        )
        session.add_all([file_one, file_two])
        session.flush()
        episodes = [
            MediaItem(
                integration_id=integration.id,
                source_type=SourceType.SONARR,
                external_item_id="101",
                external_series_id="7",
                external_web_path="/series/demo-show",
                media_type=MediaType.EPISODE,
                title="Part One",
                series_title="Demo Show",
                season_number=1,
                episode_number=1,
                monitored=True,
                file_presence=True,
            ),
            MediaItem(
                integration_id=integration.id,
                source_type=SourceType.SONARR,
                external_item_id="201",
                external_series_id="7",
                external_web_path="/series/demo-show",
                media_type=MediaType.EPISODE,
                title="Second Season",
                series_title="Demo Show",
                season_number=2,
                episode_number=1,
                monitored=True,
                file_presence=True,
            ),
        ]
        session.add_all(episodes)
        session.flush()
        session.add_all(
            [
                MediaItemFileLink(media_item_id=episodes[0].id, media_file_id=file_one.id),
                MediaItemFileLink(media_item_id=episodes[1].id, media_file_id=file_two.id),
            ]
        )
        session.commit()
        integration_id = integration.id

    with TestClient(create_app()) as client:
        series_response = client.get("/api/v1/series")
        seasons_response = client.get(f"/api/v1/series/{integration_id}/7/seasons")

    assert series_response.status_code == 200
    series_payload = series_response.json()
    assert series_payload[0]["title"] == "Demo Show"
    assert series_payload[0]["episode_count"] == 2
    assert series_payload[0]["episodes_missing_czech_audio"] == 1
    assert series_payload[0]["source_web_url"] == "https://sonarr.test/series/demo-show"

    assert seasons_response.status_code == 200
    seasons_payload = seasons_response.json()
    assert [season["season_number"] for season in seasons_payload] == [1, 2]
    assert seasons_payload[0]["episodes_missing_czech_audio"] == 1
