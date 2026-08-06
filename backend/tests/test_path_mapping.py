from pathlib import Path

from fastapi.testclient import TestClient

from app.db.session import SessionLocal, initialize_database
from app.main import create_app
from app.models.enums import SourceType
from app.models.path_mapping import AllowedMediaRoot, PathMapping
from app.services.path_mapping import map_remote_path, validate_allowed_media_root


def clear_media_roots() -> None:
    initialize_database()
    with SessionLocal() as session:
        session.query(AllowedMediaRoot).delete()
        session.commit()


def test_longest_prefix_mapping_wins() -> None:
    mappings = [
        PathMapping(
            id=1,
            remote_path_prefix="/data",
            local_path_prefix="/media",
            enabled=True,
            priority=10,
        ),
        PathMapping(
            id=2,
            remote_path_prefix="/data/movies",
            local_path_prefix="/movies",
            enabled=True,
            priority=100,
        ),
    ]

    result = map_remote_path(
        remote_path="/data/movies/Avatar (2009)/Avatar.mkv",
        source_type=SourceType.RADARR,
        integration_id=1,
        mappings=mappings,
    )

    assert result.status == "mapped"
    assert result.mapping_id == 2
    assert result.mapped_path == "/movies/Avatar (2009)/Avatar.mkv"


def test_prefix_matching_does_not_match_substrings() -> None:
    mappings = [
        PathMapping(
            id=1,
            remote_path_prefix="/data/movie",
            local_path_prefix="/movies",
            enabled=True,
            priority=1,
        )
    ]

    result = map_remote_path(
        remote_path="/data/movies/file.mkv",
        source_type=SourceType.RADARR,
        integration_id=1,
        mappings=mappings,
    )

    assert result.status == "path_not_mapped"


def test_allowed_media_root_blocks_traversal(tmp_path: Path) -> None:
    root = tmp_path / "media"
    outside = tmp_path / "outside.mkv"
    root.mkdir()
    roots = [AllowedMediaRoot(path=str(root), enabled=True)]

    assert validate_allowed_media_root(str(root / "Movie" / "file.mkv"), roots) is True
    assert validate_allowed_media_root(str(root / ".." / outside.name), roots) is False


def test_create_media_root_is_idempotent_for_existing_path() -> None:
    clear_media_roots()
    with TestClient(create_app()) as client:
        first_response = client.post(
            "/api/v1/media-roots",
            json={"path": "/movies", "enabled": True},
        )
        second_response = client.post(
            "/api/v1/media-roots",
            json={"path": "/movies", "enabled": False, "description": "Updated"},
        )
        list_response = client.get("/api/v1/media-roots")

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["enabled"] is False
    assert second_response.json()["description"] == "Updated"
    assert len(list_response.json()) == 1
