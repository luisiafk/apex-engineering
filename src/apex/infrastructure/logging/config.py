from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Configuration for the APEX logging system."""

    level: str = "INFO"
    log_dir: Path = Path("logs")
    filename: str = "apex.log"
    console_enabled: bool = True
    file_enabled: bool = True
    max_bytes: int = 5 * 1024 * 1024
    backup_count: int = 3

    def __post_init__(self) -> None:
        normalized_level = self.level.upper()

        valid_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if normalized_level not in valid_levels:
            raise ValueError(f"Invalid logging level: {self.level}")

        object.__setattr__(self, "level", normalized_level)

        if not self.filename.strip():
            raise ValueError("Log filename cannot be empty.")

        if Path(self.filename).name != self.filename:
            raise ValueError("Filename must not contain directory componenets.")

        if not self.console_enabled and not self.file_enabled:
            raise ValueError("At least one logging handler must be enabled.")

        if self.max_bytes <= 0:
            raise ValueError("max_bytes must be greater than zero.")

        if self.backup_count < 0:
            raise ValueError("backupt_count cannot be negative.")
