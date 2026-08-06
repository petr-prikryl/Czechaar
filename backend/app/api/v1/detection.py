from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.schemas.detection import (
    CzechDetectionPreviewRequest,
    CzechDetectionPreviewResponse,
    CzechDetectionSettings,
)
from app.services.czech_detection import detect_czech_audio
from app.services.detection_settings import (
    detection_config_from_settings,
    get_detection_settings,
    reset_detection_settings,
    save_detection_settings,
)

router = APIRouter(tags=["detection"])


@router.get("/czech-detection-settings", response_model=CzechDetectionSettings)
def read_czech_detection_settings(
    session: Session = Depends(get_session),
) -> CzechDetectionSettings:
    return get_detection_settings(session)


@router.put("/czech-detection-settings", response_model=CzechDetectionSettings)
def update_czech_detection_settings(
    payload: CzechDetectionSettings,
    session: Session = Depends(get_session),
) -> CzechDetectionSettings:
    return save_detection_settings(session, payload)


@router.post("/czech-detection-settings/reset", response_model=CzechDetectionSettings)
def reset_czech_detection_settings(
    session: Session = Depends(get_session),
) -> CzechDetectionSettings:
    return reset_detection_settings(session)


@router.post("/czech-detection-settings/preview", response_model=CzechDetectionPreviewResponse)
def preview_czech_detection(
    payload: CzechDetectionPreviewRequest,
    session: Session = Depends(get_session),
) -> CzechDetectionPreviewResponse:
    settings = payload.settings or get_detection_settings(session)
    result = detect_czech_audio(
        language=payload.language,
        title=payload.title,
        config=detection_config_from_settings(settings),
    )
    return CzechDetectionPreviewResponse(
        czech_match=result.czech_match,
        match_reason=result.match_reason.value,
        matched_value=result.matched_value,
    )
