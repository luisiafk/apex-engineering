import logging
from logging.handlers import RotatingFileHandler
from threading import RLock

from apex.infrastructure.logging.config import LoggingConfig
from apex.infrastructure.logging.formatters import (
    JSONFormatter,
    StandardFormatter,
)

_APEX_LOGGER_NAME = "apex"
_LOCK = RLock()


def configure_logging(config: LoggingConfig) -> None:
    """Configure the central APEX logging system."""

    with _LOCK:
        logger = logging.getLogger(_APEX_LOGGER_NAME)

        # Remove and close previously configured handlers.
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

        logger.setLevel(config.level)
        logger.propagate = False

        if config.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(config.level)
            console_handler.setFormatter(StandardFormatter())

            logger.addHandler(console_handler)

        if config.file_enabled:
            config.log_dir.mkdir(parents=True, exist_ok=True)

            log_path = config.log_dir / config.filename

            file_handler = RotatingFileHandler(
                filename=log_path,
                maxBytes=config.max_bytes,
                backupCount=config.backup_count,
                encoding="utf-8",
            )

            file_handler.setLevel(config.level)
            file_handler.setFormatter(JSONFormatter())

            logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger belonging to the APEX hierarchy."""

    if not name or not name.strip():
        raise ValueError("Logger name cannot be empty.")

    return logging.getLogger(name)
