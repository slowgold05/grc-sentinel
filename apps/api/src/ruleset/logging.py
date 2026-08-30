import logging
from collections.abc import Mapping
from typing import Any


SENSITIVE_FIELDS = frozenset(
    {"authorization", "content", "document_text", "evidence_quote", "password", "prompt", "token"}
)


def redact(value: Any) -> Any:
    """Replace values of known-sensitive fields in nested log data."""
    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]" if str(key).lower() in SENSITIVE_FIELDS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return type(value)(redact(item) for item in value)
    return value


class SensitiveDataFilter(logging.Filter):
    """Redact structured log messages and arguments before handlers receive them."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.msg)
        record.args = redact(record.args)
        return True


def configure_logging() -> None:
    """Install sensitive-data redaction for every subsequently created log record."""
    factory = logging.getLogRecordFactory()
    if getattr(factory, "redacts_sensitive_data", False):
        return

    def redacting_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = factory(*args, **kwargs)
        SensitiveDataFilter().filter(record)
        return record

    redacting_factory.redacts_sensitive_data = True  # type: ignore[attr-defined]
    logging.setLogRecordFactory(redacting_factory)
