from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


class UrlValidationError(ValueError):
    pass


def normalize_base_url(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise UrlValidationError("URL is required.")

    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise UrlValidationError("Only http and https URLs are supported.")
    if not parsed.netloc:
        raise UrlValidationError("URL must include a host.")
    if parsed.username or parsed.password:
        raise UrlValidationError("Credentials are not allowed in integration URLs.")
    if parsed.query or parsed.fragment:
        raise UrlValidationError("Query strings and fragments are not allowed in integration URLs.")

    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, path, "", ""))
