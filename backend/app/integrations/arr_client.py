from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.logging import redact_secret
from app.core.url import normalize_base_url
from app.integrations.errors import IntegrationConnectionResult
from app.models.enums import SourceType


class ArrApiClient:
    expected_source_type: SourceType

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        api_key_env_var: str | None = None,
        timeout_seconds: float = 30.0,
        verify_tls: bool = True,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.api_key = api_key
        self.api_key_env_var = api_key_env_var
        self.timeout_seconds = timeout_seconds
        self.verify_tls = verify_tls
        self.transport = transport

    def _resolved_api_key(self) -> str | None:
        if self.api_key:
            return self.api_key
        if self.api_key_env_var:
            return os.getenv(self.api_key_env_var)
        return None

    def _headers(self) -> dict[str, str]:
        api_key = self._resolved_api_key()
        if not api_key:
            return {}
        return {"X-Api-Key": api_key}

    async def get_api_json(self, path: str) -> tuple[int, Any | None, str | None]:
        url = f"{self.base_url}/api/v3/{path.lstrip('/')}"
        headers = self._headers()
        timeout = httpx.Timeout(self.timeout_seconds)
        async with httpx.AsyncClient(
            timeout=timeout,
            verify=self.verify_tls,
            follow_redirects=False,
            transport=self.transport,
        ) as client:
            response = await client.get(url, headers=headers)

        if 300 <= response.status_code < 400:
            return response.status_code, None, "redirect_not_followed"
        if response.status_code in {401, 403}:
            return response.status_code, None, "authentication_failed"
        if response.status_code >= 400:
            return response.status_code, None, "http_error"

        try:
            payload = response.json()
        except ValueError:
            return response.status_code, None, "invalid_json"
        return response.status_code, payload, None

    async def get_json(self, path: str) -> tuple[int, dict[str, Any] | None, str | None]:
        status_code, payload, error_code = await self.get_api_json(path)
        if error_code:
            return status_code, None, error_code
        if not isinstance(payload, dict):
            return status_code, None, "invalid_json"
        return status_code, payload, None

    async def get_list(self, path: str) -> list[dict[str, Any]]:
        status_code, payload, error_code = await self.get_api_json(path)
        if error_code:
            raise ArrApiError(status_code=status_code, error_code=error_code)
        if not isinstance(payload, list):
            raise ArrApiError(status_code=status_code, error_code="invalid_json")
        return [item for item in payload if isinstance(item, dict)]

    async def test_connection(self) -> IntegrationConnectionResult:
        if not self._resolved_api_key():
            return IntegrationConnectionResult(
                ok=False,
                status_code=None,
                error_code="api_key_missing",
                message="API key is not configured.",
            )

        try:
            status_code, payload, error_code = await self.get_json("system/status")
        except httpx.TimeoutException:
            return IntegrationConnectionResult(
                ok=False,
                status_code=None,
                error_code="timeout",
                message="The request timed out.",
            )
        except httpx.ConnectError as exc:
            return IntegrationConnectionResult(
                ok=False,
                status_code=None,
                error_code="connection_failed",
                message=redact_secret(str(exc)),
            )
        except httpx.TransportError as exc:
            return IntegrationConnectionResult(
                ok=False,
                status_code=None,
                error_code="transport_error",
                message=redact_secret(str(exc)),
            )

        if error_code or payload is None:
            return IntegrationConnectionResult(
                ok=False,
                status_code=status_code,
                error_code=error_code,
                message=_message_for_error(error_code),
            )

        app_name = str(payload.get("appName") or payload.get("instanceName") or "")
        version = str(payload.get("version") or "")
        if version == "":
            return IntegrationConnectionResult(
                ok=False,
                status_code=status_code,
                error_code="unexpected_response",
                message="The server did not return expected API version metadata.",
                application=app_name or None,
                version=None,
            )

        return IntegrationConnectionResult(
            ok=True,
            status_code=status_code,
            error_code=None,
            message="Connection test succeeded.",
            application=app_name or self.expected_source_type.value,
            version=version,
        )


def _message_for_error(error_code: str | None) -> str:
    if error_code is None:
        return "Connection test failed."
    return {
        "redirect_not_followed": (
            "The server returned a redirect, so the API key was not forwarded."
        ),
        "authentication_failed": "Authentication failed. Check the API key.",
        "http_error": "The server returned an error status.",
        "invalid_json": "The server returned invalid JSON.",
    }.get(error_code, "Connection test failed.")


class RadarrClient(ArrApiClient):
    expected_source_type = SourceType.RADARR

    async def list_movies(self) -> list[dict[str, Any]]:
        return await self.get_list("movie")


class SonarrClient(ArrApiClient):
    expected_source_type = SourceType.SONARR

    async def list_series(self) -> list[dict[str, Any]]:
        return await self.get_list("series")

    async def list_episodes(self, series_id: int) -> list[dict[str, Any]]:
        return await self.get_list(f"episode?seriesId={series_id}")

    async def list_episode_files(self, series_id: int) -> list[dict[str, Any]]:
        return await self.get_list(f"episodefile?seriesId={series_id}")


class ArrApiError(RuntimeError):
    def __init__(self, *, status_code: int | None, error_code: str) -> None:
        super().__init__(f"Arr API request failed: {error_code}")
        self.status_code = status_code
        self.error_code = error_code
