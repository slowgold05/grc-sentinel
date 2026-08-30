import logging

from ruleset.logging import SensitiveDataFilter


def test_sensitive_fields_are_redacted_recursively() -> None:
    record = logging.LogRecord(
        "ruleset",
        logging.INFO,
        __file__,
        1,
        {"engagement_id": "safe", "request": {"prompt": "secret", "token": "secret"}},
        (),
        None,
    )

    assert SensitiveDataFilter().filter(record)
    assert record.msg == {
        "engagement_id": "safe",
        "request": {"prompt": "[REDACTED]", "token": "[REDACTED]"},
    }
