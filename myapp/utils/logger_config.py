# utils/logger_config.py

import logging
import os
import sys
from typing import Optional
import logging.config


def _get_log_level() -> str:
    """Read LOG_LEVEL from environment, default to INFO."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def _create_formatter() -> logging.Formatter:
    """Create and return a standard log formatter."""
    return logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _create_console_handler(formatter: logging.Formatter) -> logging.Handler:
    """Create a console (stream) handler with the given formatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    return handler


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.
    Handles both TTY and non-TTY environments.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler - handle both TTY and non-TTY
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def init_logging() -> None:
    """
    Initialize logging configuration for the entire application.
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler("auto_close.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Configure werkzeug logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(console_handler)
    werkzeug_logger.addHandler(file_handler)


__all__ = ["get_logger"]
