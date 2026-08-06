from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from app.models.enums import CzechMatchReason

DEFAULT_LANGUAGE_CODES = frozenset({"cs", "cz", "ces", "cze"})
DEFAULT_TITLE_INDICATORS = frozenset(
    {
        "czech",
        "čeština",
        "cestina",
        "česky",
        "cesky",
        "český",
        "cesky dabing",
        "český dabing",
        "cz dabing",
        "czech dubbing",
    }
)


@dataclass(frozen=True, slots=True)
class CzechDetectionConfig:
    language_codes: frozenset[str] = field(default_factory=lambda: DEFAULT_LANGUAGE_CODES)
    title_indicators: frozenset[str] = field(default_factory=lambda: DEFAULT_TITLE_INDICATORS)
    custom_language_codes: frozenset[str] = field(default_factory=frozenset)
    custom_title_indicators: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class CzechDetectionResult:
    czech_match: bool
    match_reason: CzechMatchReason
    matched_value: str | None


def normalize_metadata(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized or None


def detect_czech_audio(
    *,
    language: str | None,
    title: str | None,
    config: CzechDetectionConfig | None = None,
) -> CzechDetectionResult:
    active_config = config or CzechDetectionConfig()
    default_codes = {normalize_metadata(item) for item in active_config.language_codes}
    custom_codes = {normalize_metadata(item) for item in active_config.custom_language_codes}
    normalized_language = normalize_metadata(language)
    if normalized_language:
        if normalized_language in default_codes:
            return CzechDetectionResult(True, CzechMatchReason.LANGUAGE_CODE, normalized_language)
        if normalized_language in custom_codes:
            return CzechDetectionResult(
                True,
                CzechMatchReason.CUSTOM_LANGUAGE_CODE,
                normalized_language,
            )

    normalized_title = normalize_metadata(title)
    if normalized_title:
        for indicator in sorted(active_config.title_indicators, key=len, reverse=True):
            normalized_indicator = normalize_metadata(indicator)
            if normalized_indicator and _indicator_matches(normalized_title, normalized_indicator):
                return CzechDetectionResult(
                    True,
                    CzechMatchReason.STREAM_TITLE,
                    normalized_indicator,
                )
        for indicator in sorted(active_config.custom_title_indicators, key=len, reverse=True):
            normalized_indicator = normalize_metadata(indicator)
            if normalized_indicator and _indicator_matches(normalized_title, normalized_indicator):
                return CzechDetectionResult(
                    True,
                    CzechMatchReason.CUSTOM_TITLE_INDICATOR,
                    normalized_indicator,
                )

    return CzechDetectionResult(False, CzechMatchReason.NO_MATCH, None)


def _indicator_matches(title: str, indicator: str) -> bool:
    escaped = re.escape(indicator)
    if len(indicator) <= 3:
        return re.search(rf"(?<![\w]){escaped}(?![\w])", title, flags=re.UNICODE) is not None
    return re.search(rf"(?<![\w]){escaped}(?![\w])", title, flags=re.UNICODE) is not None
