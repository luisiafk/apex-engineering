import json
import logging
from datetime import UTC, datetime
from typing import Any


class StandardFormatter(logging.Formatter):
    """Formats log records for human-readable output."""

    DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    def __init__(self) -> None:
        super().__init__(
            fmt=self.DEFAULT_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class DetailedFormatter(logging.Formatter):
    """Formats log records with additional execution information."""

    DEFAULT_FORMAT = (
        "%(asctime)s | %(levelname)s | %(name)s | "
        "PID:%(process)d | Thread:%(threadName)s | "
        "%(module)s:%(lineno)d | %(message)s"
    )

    def __init__(self) -> None:
        super().__init__(
            fmt=self.DEFAULT_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class JSONFormatter(logging.Formatter):
    """Serializes log records into structured JSON."""

    _STANDARD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(
            record.created,
            tz=UTC,
        ).isoformat(timespec="milliseconds")

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_name": record.threadName,
        }

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self._STANDARD_FIELDS
        }

        if extra_fields:
            payload["extra"] = extra_fields

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
