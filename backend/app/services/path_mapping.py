from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.enums import SourceType
from app.models.path_mapping import AllowedMediaRoot, PathMapping


@dataclass(slots=True)
class PathMappingResult:
    original_path: str
    mapped_path: str | None
    mapping_id: int | None
    status: str


def normalize_media_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    if len(normalized) > 1:
        normalized = normalized.rstrip("/")
    return normalized


def map_remote_path(
    *,
    remote_path: str,
    source_type: SourceType,
    integration_id: int,
    mappings: list[PathMapping],
) -> PathMappingResult:
    normalized_remote = normalize_media_path(remote_path)
    candidates: list[tuple[int, int, int, PathMapping]] = []
    for mapping in mappings:
        if not mapping.enabled:
            continue
        if mapping.integration_id is not None and mapping.integration_id != integration_id:
            continue
        if mapping.source_type is not None and SourceType(mapping.source_type) != source_type:
            continue
        remote_prefix = normalize_media_path(mapping.remote_path_prefix)
        if _prefix_matches(normalized_remote, remote_prefix):
            integration_specificity = 0 if mapping.integration_id == integration_id else 1
            candidates.append(
                (-len(remote_prefix), mapping.priority, integration_specificity, mapping),
            )

    if not candidates:
        return PathMappingResult(
            original_path=remote_path,
            mapped_path=None,
            mapping_id=None,
            status="path_not_mapped",
        )

    _, _, _, selected = sorted(
        candidates,
        key=lambda item: (item[0], item[1], item[2], item[3].id),
    )[0]
    remote_prefix = normalize_media_path(selected.remote_path_prefix)
    local_prefix = normalize_media_path(selected.local_path_prefix)
    suffix = normalized_remote[len(remote_prefix) :].lstrip("/")
    mapped_path = normalize_media_path(f"{local_prefix}/{suffix}" if suffix else local_prefix)
    return PathMappingResult(
        original_path=remote_path,
        mapped_path=mapped_path,
        mapping_id=selected.id,
        status="mapped",
    )


def validate_allowed_media_root(mapped_path: str, roots: list[AllowedMediaRoot]) -> bool:
    try:
        resolved_path = Path(mapped_path).resolve(strict=False)
    except (OSError, RuntimeError):
        return False
    for root in roots:
        if not root.enabled:
            continue
        try:
            resolved_root = Path(root.path).resolve(strict=False)
        except (OSError, RuntimeError):
            continue
        if resolved_path == resolved_root or resolved_path.is_relative_to(resolved_root):
            return True
    return False


def _prefix_matches(path: str, prefix: str) -> bool:
    if path == prefix:
        return True
    return path.startswith(f"{prefix}/")
