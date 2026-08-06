from enum import StrEnum


class SourceType(StrEnum):
    RADARR = "radarr"
    SONARR = "sonarr"


class MediaType(StrEnum):
    MOVIE = "movie"
    EPISODE = "episode"


class ScanState(StrEnum):
    NOT_SCANNED = "not_scanned"
    QUEUED = "queued"
    SCANNING = "scanning"
    CZECH_AUDIO_FOUND = "czech_audio_found"
    CZECH_AUDIO_MISSING = "czech_audio_missing"
    FILE_MISSING = "file_missing"
    PATH_NOT_MAPPED = "path_not_mapped"
    PATH_OUTSIDE_ALLOWED_ROOTS = "path_outside_allowed_roots"
    PATH_INACCESSIBLE = "path_inaccessible"
    FFPROBE_NOT_AVAILABLE = "ffprobe_not_available"
    FFPROBE_TIMEOUT = "ffprobe_timeout"
    FFPROBE_INVALID_OUTPUT = "ffprobe_invalid_output"
    FFPROBE_EXECUTION_ERROR = "ffprobe_execution_error"
    CANCELLED = "cancelled"
    STALE = "stale"


class SyncStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
