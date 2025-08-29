"""Logging configuration for MusicDL."""

from __future__ import annotations

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    logs_dir: Path | None = None,
    log_level: str = "INFO",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    log_format: str | None = None,
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        logs_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_file_logging: Whether to log to files
        enable_console_logging: Whether to log to console
        log_format: Custom log format string

    Returns:
        Configured root logger
    """

    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    handlers = []

    # Console handler with Rich formatting
    if enable_console_logging:
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_path=False,
            show_time=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        console_handler.setLevel(level)
        handlers.append(console_handler)

    # File handlers
    if enable_file_logging and logs_dir:
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Default log format for files
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(log_format)

        # Main log file (with rotation)
        log_file = logs_dir / "musicdl.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

        # Error log file
        error_file = logs_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        handlers.append(error_handler)

        # Session log file (new file each run)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = logs_dir / f"session_{timestamp}.log"
        session_handler = logging.FileHandler(
            session_file,
            encoding="utf-8",
        )
        session_handler.setLevel(logging.DEBUG)
        session_handler.setFormatter(formatter)
        handlers.append(session_handler)

    # Add all handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)

    # Suppress some noisy third-party loggers
    logging.getLogger("yt_dlp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


class TUILogHandler(logging.Handler):
    """Custom log handler for Textual UI."""

    def __init__(self, log_callback):
        super().__init__()
        self.log_callback = log_callback

    def emit(self, record):
        """Emit a log record to the TUI."""
        try:
            msg = self.format(record)
            if self.log_callback:
                self.log_callback(msg)
        except Exception:
            # Avoid infinite recursion if logging fails
            pass


def add_tui_handler(log_callback, level: int = logging.INFO) -> TUILogHandler:
    """Add a TUI handler to the root logger."""
    handler = TUILogHandler(log_callback)
    handler.setLevel(level)

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    logging.getLogger().addHandler(handler)
    return handler


def remove_tui_handler(handler: TUILogHandler) -> None:
    """Remove a TUI handler from the root logger."""
    logging.getLogger().removeHandler(handler)
