from __future__ import annotations

import httpx
import pytest

from app.core.logging import redact_secret
from app.core.url import UrlValidationError, normalize_base_url
from app.integrations.arr_client import RadarrClient, SonarrClient


def test_normalize_base_url_strips_trailing_slash() -> None:
    assert (
        normalize_base_url("https://radarr.example.test/base/")
        == "https://radarr.example.test/base"
    )


def test_normalize_base_url_rejects_credentials() -> None:
    with pytest.raises(UrlValidationError):
        normalize_base_url("https://user:pass@radarr.example.test")


def test_redact_secret_from_query_and_header() -> None:
    message = "failed url=http://x.local/api?apikey=secret X-Api-Key: abc123"

    assert (
        redact_secret(message)
        == "failed url=http://x.local/api?apikey=[redacted] X-Api-Key: [redacted]"
    )


@pytest.mark.asyncio
async def test_radarr_connection_uses_api_key_header() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Api-Key"] == "test-key"
        assert str(request.url) == "https://radarr.test/api/v3/system/status"
        return httpx.Response(200, json={"appName": "Radarr", "version": "5.0.0"})

    client = RadarrClient(
        base_url="https://radarr.test/",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    result = await client.test_connection()

    assert result.ok is True
    assert result.application == "Radarr"
    assert result.version == "5.0.0"


@pytest.mark.asyncio
async def test_sonarr_connection_rejects_authentication_failure() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "bad key"})

    client = SonarrClient(
        base_url="https://sonarr.test",
        api_key="bad-key",
        transport=httpx.MockTransport(handler),
    )

    result = await client.test_connection()

    assert result.ok is False
    assert result.error_code == "authentication_failed"


@pytest.mark.asyncio
async def test_connection_does_not_follow_redirects() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "https://other-host.test"})

    client = RadarrClient(
        base_url="https://radarr.test",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    result = await client.test_connection()

    assert result.ok is False
    assert result.error_code == "redirect_not_followed"
