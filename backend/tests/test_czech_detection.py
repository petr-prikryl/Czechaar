from app.models.enums import CzechMatchReason
from app.services.czech_detection import (
    CzechDetectionConfig,
    detect_czech_audio,
    normalize_metadata,
)


def test_unicode_normalization_and_whitespace() -> None:
    assert normalize_metadata("  ČEŠTINA   Dabing  ") == "čeština dabing"


def test_detects_czech_language_codes() -> None:
    result = detect_czech_audio(language="CES", title=None)

    assert result.czech_match is True
    assert result.match_reason == CzechMatchReason.LANGUAGE_CODE


def test_detects_czech_stream_title() -> None:
    result = detect_czech_audio(language="eng", title="Český dabing 5.1")

    assert result.czech_match is True
    assert result.match_reason == CzechMatchReason.STREAM_TITLE


def test_short_cz_indicator_does_not_match_inside_word() -> None:
    result = detect_czech_audio(
        language="eng",
        title="jacuzzi commentary",
        config=CzechDetectionConfig(custom_title_indicators=frozenset({"cz"})),
    )

    assert result.czech_match is False


def test_custom_language_code_reason() -> None:
    result = detect_czech_audio(
        language="czech-custom",
        title=None,
        config=CzechDetectionConfig(custom_language_codes=frozenset({"czech-custom"})),
    )

    assert result.match_reason == CzechMatchReason.CUSTOM_LANGUAGE_CODE
