from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.path_mapping import AllowedMediaRoot, PathMapping
from app.schemas.path_mapping import (
    AllowedMediaRootCreate,
    AllowedMediaRootRead,
    PathMappingCreate,
    PathMappingRead,
    PathMappingTestRequest,
    PathMappingTestResponse,
)
from app.services.path_mapping import (
    map_remote_path,
    normalize_media_path,
    validate_allowed_media_root,
)

router = APIRouter(tags=["path-safety"])


@router.get("/path-mappings", response_model=list[PathMappingRead])
def list_path_mappings(session: Session = Depends(get_session)) -> list[PathMapping]:
    statement = select(PathMapping).order_by(PathMapping.priority, PathMapping.id)
    return list(session.scalars(statement))


@router.post("/path-mappings", response_model=PathMappingRead, status_code=status.HTTP_201_CREATED)
def create_path_mapping(
    payload: PathMappingCreate,
    session: Session = Depends(get_session),
) -> PathMapping:
    mapping = PathMapping(
        integration_id=payload.integration_id,
        source_type=payload.source_type,
        remote_path_prefix=normalize_media_path(payload.remote_path_prefix),
        local_path_prefix=normalize_media_path(payload.local_path_prefix),
        enabled=payload.enabled,
        priority=payload.priority,
        description=payload.description,
    )
    session.add(mapping)
    session.commit()
    session.refresh(mapping)
    return mapping


@router.post("/path-mappings/test", response_model=PathMappingTestResponse)
def test_path_mapping(
    payload: PathMappingTestRequest,
    session: Session = Depends(get_session),
) -> PathMappingTestResponse:
    mappings = list(
        session.scalars(select(PathMapping).order_by(PathMapping.priority, PathMapping.id))
    )
    roots = list(
        session.scalars(select(AllowedMediaRoot).where(AllowedMediaRoot.enabled.is_(True)))
    )
    result = map_remote_path(
        remote_path=payload.remote_path,
        source_type=payload.source_type,
        integration_id=payload.integration_id,
        mappings=mappings,
    )
    inside_root = None
    if result.mapped_path is not None:
        inside_root = validate_allowed_media_root(result.mapped_path, roots)
    return PathMappingTestResponse(
        original_path=result.original_path,
        mapped_path=result.mapped_path,
        mapping_id=result.mapping_id,
        status=result.status,
        inside_allowed_root=inside_root,
    )


@router.delete("/path-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_path_mapping(mapping_id: int, session: Session = Depends(get_session)) -> None:
    mapping = session.get(PathMapping, mapping_id)
    if mapping is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path mapping not found.")
    session.delete(mapping)
    session.commit()


@router.get("/media-roots", response_model=list[AllowedMediaRootRead])
def list_media_roots(session: Session = Depends(get_session)) -> list[AllowedMediaRootRead]:
    roots = list(session.scalars(select(AllowedMediaRoot).order_by(AllowedMediaRoot.path)))
    return [_serialize_root(root) for root in roots]


@router.post(
    "/media-roots",
    response_model=AllowedMediaRootRead,
    status_code=status.HTTP_201_CREATED,
)
def create_media_root(
    payload: AllowedMediaRootCreate,
    session: Session = Depends(get_session),
) -> AllowedMediaRootRead:
    root = AllowedMediaRoot(
        path=normalize_media_path(payload.path),
        enabled=payload.enabled,
        description=payload.description,
    )
    session.add(root)
    session.commit()
    session.refresh(root)
    return _serialize_root(root)


@router.delete("/media-roots/{root_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media_root(root_id: int, session: Session = Depends(get_session)) -> None:
    root = session.get(AllowedMediaRoot, root_id)
    if root is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media root not found.")
    session.delete(root)
    session.commit()


def _serialize_root(root: AllowedMediaRoot) -> AllowedMediaRootRead:
    path = Path(root.path)
    return AllowedMediaRootRead.model_validate(
        {
            **root.__dict__,
            "exists": path.exists(),
            "readable": path.exists() and path.is_dir(),
        }
    )
