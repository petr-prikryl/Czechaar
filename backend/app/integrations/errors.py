from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IntegrationConnectionResult:
    ok: bool
    status_code: int | None
    error_code: str | None
    message: str
    application: str | None = None
    version: str | None = None
