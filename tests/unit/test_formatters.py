import json
import logging
import re
import sys
from datetime import UTC, datetime

import pytest

from apex.infrastructure.logging.formatters import (
    DetailedFormatter,
    JSONFormatter,
    StandardFormatter,
)


@pytest.fixture
def log_record() -> logging.LogRecord:
    record = logging.LogRecord(
        name="apex.test",
        level=logging.INFO,
        pathname="/src/apex/test_module.py",
        lineno=42,
        msg="Test message: %s",
        args=("APEX",),
        exc_info=None,
        func="test_function",
    )

    record.created = 1_700_000_000.123

    return record


class TestStandardFormatter:
    def test_formats_basic_message(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        formatter = StandardFormatter()

        result = formatter.format(log_record)

        assert "INFO" in result
        assert "apex.test" in result
        assert "Test message: APEX" in result

    def test_includes_timestamp(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        formatter = StandardFormatter()

        result = formatter.format(log_record)

        assert re.search(
            r"\d{4}-\d{2}-\d{2} "
            r"\d{2}:\d{2}:\d{2}",
            result,
        )


class TestDetailedFormatter:
    def test_includes_execution_information(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        formatter = DetailedFormatter()

        result = formatter.format(log_record)

        assert f"PID:{log_record.process}" in result
        assert f"Thread:{log_record.threadName}" in result
        assert "test_module:42" in result
        assert "Test message: APEX" in result


class TestJSONFormatter:
    def test_returns_valid_json(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        formatter = JSONFormatter()

        result = formatter.format(log_record)

        payload = json.loads(result)

        assert isinstance(payload, dict)

    def test_includes_standard_fields(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        formatter = JSONFormatter()

        payload = json.loads(formatter.format(log_record))

        assert payload["level"] == "INFO"
        assert payload["logger"] == "apex.test"
        assert payload["message"] == "Test message: APEX"
        assert payload["module"] == "test_module"
        assert payload["function"] == "test_function"
        assert payload["line"] == 42

    def test_timestamp_is_utc(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        formatter = JSONFormatter()

        payload = json.loads(formatter.format(log_record))

        expected = datetime.fromtimestamp(
            log_record.created,
            tz=UTC,
        ).isoformat(timespec="milliseconds")

        assert payload["timestamp"] == expected

    def test_preserves_extra_fields(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        log_record.experiment_id = "experiment-001"
        log_record.worker_id = 3

        formatter = JSONFormatter()

        payload = json.loads(formatter.format(log_record))

        assert payload["extra"]["experiment_id"] == "experiment-001"
        assert payload["extra"]["worker_id"] == 3

    def test_serializes_exception(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        try:
            raise ValueError("Test exception")
        except ValueError:
            log_record.exc_info = sys.exc_info()

        formatter = JSONFormatter()

        payload = json.loads(formatter.format(log_record))

        assert "exception" in payload
        assert "ValueError: Test exception" in payload["exception"]

    def test_serializes_stack_info(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        log_record.stack_info = "Test stack information"

        formatter = JSONFormatter()

        payload = json.loads(formatter.format(log_record))

        assert payload["stack_info"] == "Test stack information"

    def test_preserves_unicode(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        log_record.msg = "Aerodinámica: presión y sustentación"
        log_record.args = ()
        formatter = JSONFormatter()

        result = formatter.format(log_record)
        payload = json.loads(result)

        assert "Aerodinámica" in result
        assert payload["message"] == ("Aerodinámica: presión y sustentación")

    def test_handles_non_serializable_extra(
        self,
        log_record: logging.LogRecord,
    ) -> None:
        log_record.custom_object = object()

        formatter = JSONFormatter()

        payload = json.loads(formatter.format(log_record))

        assert isinstance(
            payload["extra"]["custom_object"],
            str,
        )
