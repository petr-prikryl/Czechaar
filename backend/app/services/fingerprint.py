from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.services.path_mapping import normalize_media_path


@dataclass(frozen=True, slots=True)
class FileFingerprint:
    value: str
    size: int
    modified_time: datetime
    modified_ns: int


def calculate_fingerprint(path: Path) -> FileFingerprint:
    stat = path.stat()
    normalized_path = normalize_media_path(str(path.resolve(strict=False)))
    material = f"{normalized_path}|{stat.st_size}|{stat.st_mtime_ns}".encode()
    return FileFingerprint(
        value=hashlib.sha256(material).hexdigest(),
        size=stat.st_size,
        modified_time=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        modified_ns=stat.st_mtime_ns,
    )
