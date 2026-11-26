import pytest
from pathlib import Path

from apex.infrastructure.logging.config import LoggingConfig


def test_default_configuration() -> None:
    config = LoggingConfig()

    assert config.level == "INFO"
    assert config.log_dir == Path("logs")
    assert config.filename == "apex.log"
    assert config.console_enabled is True
    assert config.file_enabled is True
    assert config.max_bytes == 5 * 1024 * 1024
    assert config.backup_count == 3


def test_logging_level_is_normalized() -> None:
    config = LoggingConfig(level="debug")

    assert config.level == "DEBUG"


def test_invalid_logging_level() -> None:
    with pytest.raises(ValueError):
        LoggingConfig(level="INVALID")


def test_empty_filename() -> None:
    with pytest.raises(ValueError):
        LoggingConfig(filename="")


def test_filename_with_directory() -> None:
    with pytest.raises(ValueError):
        LoggingConfig(filename="../apex.log")


def test_at_least_one_handler_required() -> None:
    with pytest.raises(ValueError):
        LoggingConfig(
            console_enabled=False,
            file_enabled=False,
        )


def test_invalid_max_bytes() -> None:
    with pytest.raises(ValueError):
        LoggingConfig(max_bytes=0)


def test_negative_backup_count() -> None:
    with pytest.raises(ValueError):
        LoggingConfig(backup_count=-1)


def test_custom_configuration() -> None:
    config = LoggingConfig(
        level="WARNING",
        log_dir=Path("custom_logs"),
        filename="simulation.log",
        max_bytes=1024,
        backup_count=5,
    )

    assert config.level == "WARNING"
    assert config.log_dir == Path("custom_logs")
    assert config.filename == "simulation.log"
    assert config.max_bytes == 1024
    assert config.backup_count == 5
