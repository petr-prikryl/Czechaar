from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.models.enums import ScanState
from app.services.ffprobe import FfprobeRunner, parse_ffprobe_output


def test_parse_ffprobe_output_detects_czech_language() -> None:
    output = """
    {"streams":[{"index":1,"codec_name":"aac","channels":2,"tags":{"language":"cze"}}]}
    """

    result = parse_ffprobe_output(output)

    assert result.state == ScanState.CZECH_AUDIO_FOUND
    assert result.streams[0].detection.matched_value == "cze"


def test_parse_ffprobe_output_detects_missing_czech() -> None:
    output = """
    {"streams":[{"index":1,"codec_name":"aac","channels":2,"tags":{"language":"eng"}}]}
    """

    result = parse_ffprobe_output(output)

    assert result.state == ScanState.CZECH_AUDIO_MISSING


def test_parse_ffprobe_output_handles_invalid_json() -> None:
    result = parse_ffprobe_output("not-json")

    assert result.state == ScanState.FFPROBE_INVALID_OUTPUT


@pytest.mark.asyncio
async def test_ffprobe_runner_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeProcess:
        returncode = None

        async def communicate(self) -> tuple[bytes, bytes]:
            await asyncio.sleep(1)
            return b"", b""

        def kill(self) -> None:
            self.returncode = -9

        async def wait(self) -> int:
            return -9

    async def fake_create_subprocess_exec(*_: object, **__: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    result = await FfprobeRunner(timeout_seconds=0).inspect_audio_streams(Path("media.mkv"))

    assert result.state == ScanState.FFPROBE_TIMEOUT
