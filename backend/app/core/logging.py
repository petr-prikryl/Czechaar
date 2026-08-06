from __future__ import annotations

import logging
import re

from app.core.config import Settings

API_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key=)[^&\s]+")
HEADER_KEY_PATTERN = re.compile(r"(?i)(x-api-key['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+")


def redact_secret(value: str) -> str:
    redacted = API_KEY_PATTERN.sub(r"\1[redacted]", value)
    return HEADER_KEY_PATTERN.sub(r"\1[redacted]", redacted)


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secret(record.msg)
        if record.args:
            record.args = tuple(redact_secret(str(arg)) for arg in record.args)
        return True


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    root_logger = logging.getLogger()
    if not any(isinstance(item, SecretRedactionFilter) for item in root_logger.filters):
        root_logger.addFilter(SecretRedactionFilter())
