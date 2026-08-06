from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models.enums import ScanState
from app.services.czech_detection import (
    CzechDetectionConfig,
    CzechDetectionResult,
    detect_czech_audio,
    normalize_metadata,
)

FFPROBE_ANALYZER_VERSION = "ffprobe-audio-v1"
MAX_CAPTURE_BYTES = 1_000_000


@dataclass(frozen=True, slots=True)
class AudioStreamInfo:
    stream_index: int
    codec_name: str | None
    codec_long_name: str | None
    channels: int | None
    channel_layout: str | None
    sample_rate: int | None
    bit_rate: int | None
    original_language: str | None
    normalized_language: str | None
    original_title: str | None
    normalized_title: str | None
    detection: CzechDetectionResult


@dataclass(frozen=True, slots=True)
class FfprobeResult:
    state: ScanState
    streams: list[AudioStreamInfo]
    error_message: str | None = None


class FfprobeRunner:
    def __init__(self, executable: str = "ffprobe", timeout_seconds: int = 60) -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    async def inspect_audio_streams(self, media_path: Path) -> FfprobeResult:
        args = [
            self.executable,
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index,codec_name,codec_long_name,channels,channel_layout,sample_rate,bit_rate:"
            "stream_tags=language,title",
            "-of",
            "json",
            str(media_path),
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return FfprobeResult(
                ScanState.FFPROBE_NOT_AVAILABLE,
                [],
                "ffprobe executable not found.",
            )
        except OSError as exc:
            return FfprobeResult(ScanState.FFPROBE_EXECUTION_ERROR, [], str(exc))

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return FfprobeResult(ScanState.FFPROBE_TIMEOUT, [], "ffprobe timed out.")

        stdout_text = _decode_limited(stdout)
        stderr_text = _decode_limited(stderr)
        if process.returncode != 0:
            return FfprobeResult(
                ScanState.FFPROBE_EXECUTION_ERROR,
                [],
                stderr_text or f"ffprobe exited with status {process.returncode}.",
            )
        return parse_ffprobe_output(stdout_text)


def parse_ffprobe_output(
    output: str,
    detection_config: CzechDetectionConfig | None = None,
) -> FfprobeResult:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        return FfprobeResult(ScanState.FFPROBE_INVALID_OUTPUT, [], str(exc))
    streams_payload = payload.get("streams") if isinstance(payload, dict) else None
    if not isinstance(streams_payload, list):
        return FfprobeResult(ScanState.FFPROBE_INVALID_OUTPUT, [], "Missing streams array.")

    streams: list[AudioStreamInfo] = []
    for stream in streams_payload:
        if not isinstance(stream, dict):
            continue
        tags = stream.get("tags") if isinstance(stream.get("tags"), dict) else {}
        language = _optional_str(tags.get("language")) if isinstance(tags, dict) else None
        title = _optional_str(tags.get("title")) if isinstance(tags, dict) else None
        detection = detect_czech_audio(language=language, title=title, config=detection_config)
        streams.append(
            AudioStreamInfo(
                stream_index=_int_or_zero(stream.get("index")),
                codec_name=_optional_str(stream.get("codec_name")),
                codec_long_name=_optional_str(stream.get("codec_long_name")),
                channels=_optional_int(stream.get("channels")),
                channel_layout=_optional_str(stream.get("channel_layout")),
                sample_rate=_optional_int(stream.get("sample_rate")),
                bit_rate=_optional_int(stream.get("bit_rate")),
                original_language=language,
                normalized_language=normalize_metadata(language),
                original_title=title,
                normalized_title=normalize_metadata(title),
                detection=detection,
            )
        )

    state = (
        ScanState.CZECH_AUDIO_FOUND
        if any(item.detection.czech_match for item in streams)
        else ScanState.CZECH_AUDIO_MISSING
    )
    return FfprobeResult(state, streams, None)


def _decode_limited(value: bytes) -> str:
    return value[:MAX_CAPTURE_BYTES].decode("utf-8", errors="replace").strip()


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_or_zero(value: Any) -> int:
    return _optional_int(value) or 0
