from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audio import AudioStream
from app.models.enums import ScanState, SourceType
from app.models.media import MediaFile
from app.models.path_mapping import AllowedMediaRoot, PathMapping
from app.services.ffprobe import FFPROBE_ANALYZER_VERSION, FfprobeRunner
from app.services.fingerprint import calculate_fingerprint
from app.services.path_mapping import map_remote_path, validate_allowed_media_root


@dataclass(slots=True)
class AnalysisOutcome:
    media_file: MediaFile
    cache_hit: bool


class MediaAnalysisService:
    def __init__(self, session: Session) -> None:
        self.session = session

    async def analyze_media_file(
        self,
        media_file_id: int,
        *,
        force: bool = False,
    ) -> AnalysisOutcome:
        media_file = self.session.get(MediaFile, media_file_id)
        if media_file is None:
            raise ValueError("Media file not found.")

        mappings = list(
            self.session.scalars(select(PathMapping).order_by(PathMapping.priority, PathMapping.id))
        )
        roots = list(
            self.session.scalars(select(AllowedMediaRoot).where(AllowedMediaRoot.enabled.is_(True)))
        )
        mapping_result = map_remote_path(
            remote_path=media_file.original_source_path,
            source_type=SourceType(media_file.source_type),
            integration_id=media_file.integration_id,
            mappings=mappings,
        )
        media_file.mapped_local_path = mapping_result.mapped_path
        media_file.last_scan_attempt = datetime.now(UTC)

        if mapping_result.mapped_path is None:
            return self._finish_with_error(
                media_file,
                ScanState.PATH_NOT_MAPPED,
                "No path mapping matched.",
            )
        if not validate_allowed_media_root(mapping_result.mapped_path, roots):
            return self._finish_with_error(
                media_file,
                ScanState.PATH_OUTSIDE_ALLOWED_ROOTS,
                "Mapped path is outside allowed media roots.",
            )

        local_path = Path(mapping_result.mapped_path)
        if not local_path.exists():
            return self._finish_with_error(
                media_file,
                ScanState.FILE_MISSING,
                "File does not exist.",
            )
        if not local_path.is_file():
            return self._finish_with_error(
                media_file,
                ScanState.PATH_INACCESSIBLE,
                "Path is not a file.",
            )

        fingerprint = calculate_fingerprint(local_path)
        if (
            not force
            and media_file.fingerprint == fingerprint.value
            and media_file.analyzer_version == FFPROBE_ANALYZER_VERSION
            and media_file.scan_state
            in {ScanState.CZECH_AUDIO_FOUND, ScanState.CZECH_AUDIO_MISSING}
        ):
            self.session.add(media_file)
            self.session.commit()
            self.session.refresh(media_file)
            return AnalysisOutcome(media_file=media_file, cache_hit=True)

        settings = get_settings()
        runner = FfprobeRunner(settings.ffprobe_path, settings.ffprobe_timeout)
        result = await runner.inspect_audio_streams(local_path)
        self.session.execute(delete(AudioStream).where(AudioStream.media_file_id == media_file.id))
        for stream in result.streams:
            self.session.add(
                AudioStream(
                    media_file_id=media_file.id,
                    stream_index=stream.stream_index,
                    codec_name=stream.codec_name,
                    codec_long_name=stream.codec_long_name,
                    channels=stream.channels,
                    channel_layout=stream.channel_layout,
                    sample_rate=stream.sample_rate,
                    bit_rate=stream.bit_rate,
                    original_language=stream.original_language,
                    normalized_language=stream.normalized_language,
                    original_title=stream.original_title,
                    normalized_title=stream.normalized_title,
                    czech_match=stream.detection.czech_match,
                    match_reason=stream.detection.match_reason,
                    matched_value=stream.detection.matched_value,
                )
            )

        media_file.scan_state = result.state
        media_file.czech_audio_result = (
            result.state == ScanState.CZECH_AUDIO_FOUND
            if result.state in {ScanState.CZECH_AUDIO_FOUND, ScanState.CZECH_AUDIO_MISSING}
            else None
        )
        media_file.analyzer_version = FFPROBE_ANALYZER_VERSION
        media_file.fingerprint = fingerprint.value
        media_file.size = fingerprint.size
        media_file.modified_time = fingerprint.modified_time
        media_file.error_code = None if result.error_message is None else result.state.value
        media_file.sanitized_error_message = result.error_message
        if result.state in {ScanState.CZECH_AUDIO_FOUND, ScanState.CZECH_AUDIO_MISSING}:
            media_file.last_successful_scan = datetime.now(UTC)
        self.session.add(media_file)
        self.session.commit()
        self.session.refresh(media_file)
        return AnalysisOutcome(media_file=media_file, cache_hit=False)

    def _finish_with_error(
        self,
        media_file: MediaFile,
        state: ScanState,
        message: str,
    ) -> AnalysisOutcome:
        media_file.scan_state = state
        media_file.czech_audio_result = None
        media_file.error_code = state.value
        media_file.sanitized_error_message = message
        self.session.add(media_file)
        self.session.commit()
        self.session.refresh(media_file)
        return AnalysisOutcome(media_file=media_file, cache_hit=False)
