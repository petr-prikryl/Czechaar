from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from app.models.setting import ApplicationSetting
from app.schemas.detection import CzechDetectionSettings
from app.services.czech_detection import (
    DEFAULT_LANGUAGE_CODES,
    DEFAULT_TITLE_INDICATORS,
    CzechDetectionConfig,
    normalize_metadata,
)

DETECTION_SETTINGS_KEY = "czech_detection_settings"


def default_detection_settings() -> CzechDetectionSettings:
    return CzechDetectionSettings(
        language_codes=sorted(DEFAULT_LANGUAGE_CODES),
        title_indicators=sorted(DEFAULT_TITLE_INDICATORS),
    )


def get_detection_settings(session: Session) -> CzechDetectionSettings:
    setting = session.get(ApplicationSetting, DETECTION_SETTINGS_KEY)
    if setting is None:
        return default_detection_settings()
    try:
        payload = json.loads(setting.value)
        return _normalize_settings(CzechDetectionSettings.model_validate(payload))
    except (ValueError, TypeError):
        return default_detection_settings()


def save_detection_settings(
    session: Session,
    settings: CzechDetectionSettings,
) -> CzechDetectionSettings:
    normalized = _normalize_settings(settings)
    payload = normalized.model_dump_json()
    setting = session.get(ApplicationSetting, DETECTION_SETTINGS_KEY)
    if setting is None:
        session.add(ApplicationSetting(key=DETECTION_SETTINGS_KEY, value=payload))
    else:
        setting.value = payload
        session.add(setting)
    session.commit()
    return normalized


def reset_detection_settings(session: Session) -> CzechDetectionSettings:
    setting = session.get(ApplicationSetting, DETECTION_SETTINGS_KEY)
    if setting is not None:
        session.delete(setting)
        session.commit()
    return default_detection_settings()


def detection_config_from_settings(settings: CzechDetectionSettings) -> CzechDetectionConfig:
    active_codes = frozenset(settings.language_codes)
    active_indicators = frozenset(settings.title_indicators)
    default_codes = frozenset(code for code in DEFAULT_LANGUAGE_CODES if code in active_codes)
    default_indicators = frozenset(
        indicator for indicator in DEFAULT_TITLE_INDICATORS if indicator in active_indicators
    )
    return CzechDetectionConfig(
        language_codes=default_codes,
        title_indicators=default_indicators,
        custom_language_codes=active_codes - DEFAULT_LANGUAGE_CODES,
        custom_title_indicators=active_indicators - DEFAULT_TITLE_INDICATORS,
    )


def detection_settings_version(settings: CzechDetectionSettings) -> str:
    payload = settings.model_dump_json()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _normalize_settings(settings: CzechDetectionSettings) -> CzechDetectionSettings:
    language_codes = _normalize_unique(settings.language_codes)
    title_indicators = _normalize_unique(settings.title_indicators)
    return CzechDetectionSettings(
        language_codes=language_codes or default_detection_settings().language_codes,
        title_indicators=title_indicators or default_detection_settings().title_indicators,
    )


def _normalize_unique(values: list[str]) -> list[str]:
    normalized = {value for item in values if (value := normalize_metadata(item))}
    return sorted(normalized)
