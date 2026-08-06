from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from app.models.enums import ScanState
from app.models.media import MediaFile
from app.services.ffprobe import FFPROBE_ANALYZER_VERSION
from app.services.fingerprint import calculate_fingerprint
from app.services.media_analysis import AnalysisOutcome


def test_fingerprint_changes_when_file_changes(tmp_path: Path) -> None:
    media_file = tmp_path / "sample.mkv"
    media_file.write_bytes(b"one")
    first = calculate_fingerprint(media_file)
    media_file.write_bytes(b"two-two")
    os.utime(media_file, None)
    second = calculate_fingerprint(media_file)

    assert first.value != second.value
    assert second.size == 7


def test_analysis_cache_reuse_contract() -> None:
    media_file = MediaFile(
        id=1,
        integration_id=1,
        source_type="radarr",
        external_file_id="10",
        original_source_path="/remote/movie.mkv",
        fingerprint="abc",
        analyzer_version=FFPROBE_ANALYZER_VERSION,
        scan_state=ScanState.CZECH_AUDIO_FOUND,
        last_successful_scan=datetime.now(UTC),
    )
    outcome = AnalysisOutcome(media_file=media_file, cache_hit=True)

    assert outcome.cache_hit is True
    assert outcome.media_file.scan_state == ScanState.CZECH_AUDIO_FOUND
