from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.integrations.arr_client import RadarrClient, SonarrClient
from app.integrations.errors import IntegrationConnectionResult
from app.models.enums import SourceType
from app.models.integration import Integration
from app.repositories.integrations import IntegrationRepository
from app.schemas.integration import (
    IntegrationConnectionTestRequest,
    IntegrationConnectionTestResponse,
    IntegrationCreate,
    IntegrationRead,
    IntegrationUpdate,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationRead])
def list_integrations(session: Session = Depends(get_session)) -> list[Integration]:
    return IntegrationRepository(session).list()


@router.post("", response_model=IntegrationRead, status_code=status.HTTP_201_CREATED)
def create_integration(
    payload: IntegrationCreate,
    session: Session = Depends(get_session),
) -> Integration:
    integration = Integration(
        source_type=payload.source_type,
        name=payload.name.strip(),
        base_url=payload.base_url,
        web_url=payload.web_url,
        api_key=payload.api_key or None,
        api_key_env_var=payload.api_key_env_var,
        enabled=payload.enabled,
        timeout_seconds=payload.timeout_seconds,
        verify_tls=payload.verify_tls,
    )
    return IntegrationRepository(session).add(integration)


@router.post("/test", response_model=IntegrationConnectionTestResponse)
async def test_unsaved_integration(
    payload: IntegrationConnectionTestRequest,
) -> IntegrationConnectionTestResponse:
    result = await _test_connection(
        source_type=payload.source_type,
        base_url=payload.base_url,
        api_key=payload.api_key,
        api_key_env_var=payload.api_key_env_var,
        timeout_seconds=payload.timeout_seconds,
        verify_tls=payload.verify_tls,
    )
    return _serialize_result(result)


@router.get("/{integration_id}", response_model=IntegrationRead)
def get_integration(integration_id: int, session: Session = Depends(get_session)) -> Integration:
    integration = IntegrationRepository(session).get(integration_id)
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found.")
    return integration


@router.patch("/{integration_id}", response_model=IntegrationRead)
def update_integration(
    integration_id: int,
    payload: IntegrationUpdate,
    session: Session = Depends(get_session),
) -> Integration:
    repository = IntegrationRepository(session)
    integration = repository.get(integration_id)
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "name" and isinstance(value, str):
            value = value.strip()
        if key == "api_key" and value == "":
            value = None
        setattr(integration, key, value)
    return repository.commit(integration)


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration(integration_id: int, session: Session = Depends(get_session)) -> None:
    repository = IntegrationRepository(session)
    integration = repository.get(integration_id)
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found.")
    repository.delete(integration)


@router.post("/{integration_id}/test", response_model=IntegrationConnectionTestResponse)
async def test_saved_integration(
    integration_id: int,
    session: Session = Depends(get_session),
) -> IntegrationConnectionTestResponse:
    repository = IntegrationRepository(session)
    integration = repository.get(integration_id)
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found.")

    result = await _test_connection(
        source_type=integration.source_type,
        base_url=integration.base_url,
        api_key=integration.api_key,
        api_key_env_var=integration.api_key_env_var,
        timeout_seconds=integration.timeout_seconds,
        verify_tls=integration.verify_tls,
    )
    integration.last_test_at = datetime.now(UTC)
    repository.commit(integration)
    return _serialize_result(result)


async def _test_connection(
    *,
    source_type: SourceType,
    base_url: str,
    api_key: str | None,
    api_key_env_var: str | None,
    timeout_seconds: float,
    verify_tls: bool,
) -> IntegrationConnectionResult:
    client_cls = RadarrClient if source_type == SourceType.RADARR else SonarrClient
    client = client_cls(
        base_url=base_url,
        api_key=api_key,
        api_key_env_var=api_key_env_var,
        timeout_seconds=timeout_seconds,
        verify_tls=verify_tls,
    )
    return await client.test_connection()


def _serialize_result(result: IntegrationConnectionResult) -> IntegrationConnectionTestResponse:
    return IntegrationConnectionTestResponse(
        ok=result.ok,
        status_code=result.status_code,
        error_code=result.error_code,
        message=result.message,
        application=result.application,
        version=result.version,
    )
