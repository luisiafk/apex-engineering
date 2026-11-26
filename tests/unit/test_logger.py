import json
import logging

import pytest

from apex.infrastructure.logging.config import LoggingConfig
from apex.infrastructure.logging.logger import (
    configure_logging,
    get_logger,
)


@pytest.fixture
def clean_apex_logger():
    """Provides an isolated APEX logger for each test."""

    logger = logging.getLogger("apex")

    original_handlers = logger.handlers[:]
    original_level = logger.level
    original_propagate = logger.propagate

    for handler in original_handlers:
        logger.removeHandler(handler)

    yield logger

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    for handler in original_handlers:
        logger.addHandler(handler)

    logger.setLevel(original_level)
    logger.propagate = original_propagate


@pytest.fixture
def logging_config(tmp_path):
    """Provides a default logging configuration."""

    return LoggingConfig(
        level="INFO",
        log_dir=tmp_path,
        filename="apex.log",
        console_enabled=True,
        file_enabled=True,
    )


class TestConfigureLogging:
    def test_configures_apex_logger(
        self,
        clean_apex_logger,
        logging_config,
    ):
        configure_logging(logging_config)

        assert clean_apex_logger.level == logging.INFO

    def test_respects_configured_log_level(
        self,
        clean_apex_logger,
        logging_config,
        capsys,
    ):
        configure_logging(logging_config)

        logger = get_logger("apex.test")

        logger.debug("Debug message")
        logger.info("Information message")

        output = capsys.readouterr().err

        assert "Debug message" not in output
        assert "Information message" in output

    def test_console_uses_readable_format(
        self,
        clean_apex_logger,
        logging_config,
        capsys,
    ):
        configure_logging(logging_config)

        logger = get_logger("apex.test")
        logger.info("Console test")

        output = capsys.readouterr().err

        assert "INFO" in output
        assert "apex.test" in output
        assert "Console test" in output

    def test_file_uses_json_format(
        self,
        clean_apex_logger,
        logging_config,
    ):
        configure_logging(logging_config)

        logger = get_logger("apex.test")
        logger.info("JSON test")

        log_file = logging_config.log_dir / logging_config.filename

        payload = json.loads(log_file.read_text(encoding="utf-8"))

        assert payload["level"] == "INFO"
        assert payload["logger"] == "apex.test"
        assert payload["message"] == "JSON test"

    def test_creates_log_directory(
        self,
        clean_apex_logger,
        tmp_path,
    ):
        log_dir = tmp_path / "nested" / "logs"

        config = LoggingConfig(
            log_dir=log_dir,
            filename="apex.log",
        )

        configure_logging(config)

        assert log_dir.exists()
        assert (log_dir / "apex.log").exists()

    def test_reconfiguration_does_not_duplicate_messages(
        self,
        clean_apex_logger,
        logging_config,
        capsys,
    ):
        configure_logging(logging_config)
        configure_logging(logging_config)

        logger = get_logger("apex.test")
        logger.info("Single message")

        output = capsys.readouterr().err

        log_file = logging_config.log_dir / logging_config.filename
        file_lines = log_file.read_text(encoding="utf-8").splitlines()

        assert output.count("Single message") == 1
        assert len(file_lines) == 1

    def test_does_not_modify_python_root_logger(
        self,
        clean_apex_logger,
        logging_config,
    ):
        root_logger = logging.getLogger()

        original_level = root_logger.level
        original_handlers = root_logger.handlers[:]

        configure_logging(logging_config)

        assert root_logger.level == original_level
        assert root_logger.handlers == original_handlers

    def test_child_loggers_use_apex_configuration(
        self,
        clean_apex_logger,
        logging_config,
    ):
        configure_logging(logging_config)

        parent = get_logger("apex")
        child = get_logger("apex.aerodynamics")

        assert child.parent is parent
        assert child.getEffectiveLevel() == logging.INFO

    def test_console_only_configuration(
        self,
        clean_apex_logger,
        tmp_path,
        capsys,
    ):
        config = LoggingConfig(
            log_dir=tmp_path,
            console_enabled=True,
            file_enabled=False,
        )

        configure_logging(config)

        logger = get_logger("apex.test")
        logger.info("Console only")

        output = capsys.readouterr().err

        assert "Console only" in output
        assert not (tmp_path / config.filename).exists()

    def test_file_only_configuration(
        self,
        clean_apex_logger,
        tmp_path,
        capsys,
    ):
        config = LoggingConfig(
            log_dir=tmp_path,
            console_enabled=False,
            file_enabled=True,
        )

        configure_logging(config)

        logger = get_logger("apex.test")
        logger.info("File only")

        output = capsys.readouterr().err

        log_file = tmp_path / config.filename
        payload = json.loads(log_file.read_text(encoding="utf-8"))

        assert "File only" not in output
        assert payload["message"] == "File only"


class TestLogRotation:
    def test_rotates_file_when_max_size_is_reached(
        self,
        clean_apex_logger,
        tmp_path,
    ):
        config = LoggingConfig(
            level="INFO",
            log_dir=tmp_path,
            filename="apex.log",
            console_enabled=False,
            file_enabled=True,
            max_bytes=300,
            backup_count=2,
        )

        configure_logging(config)

        logger = get_logger("apex.test")

        for index in range(10):
            logger.info("Message %s: %s", index, "x" * 100)

        rotated_file = tmp_path / "apex.log.1"

        assert rotated_file.exists()

    def test_respects_backup_count(
        self,
        clean_apex_logger,
        tmp_path,
    ):
        config = LoggingConfig(
            level="INFO",
            log_dir=tmp_path,
            filename="apex.log",
            console_enabled=False,
            file_enabled=True,
            max_bytes=300,
            backup_count=2,
        )

        configure_logging(config)

        logger = get_logger("apex.test")

        for index in range(20):
            logger.info("Message %s: %s", index, "x" * 100)

        assert (tmp_path / "apex.log.1").exists()
        assert (tmp_path / "apex.log.2").exists()
        assert not (tmp_path / "apex.log.3").exists()

    def test_rejects_empty_logger_name(self):
        with pytest.raises(ValueError):
            get_logger("")
