"""Logging configuration for the application."""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure application logging with consistent format.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
              Defaults to INFO if not specified
    """
    log_level = getattr(logging, level.upper() if level else "INFO")

    # Create formatter with timestamp, level, and correlation ID support
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from AWS SDK
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info(f"Logging configured at {logging.getLevelName(log_level)} level")
