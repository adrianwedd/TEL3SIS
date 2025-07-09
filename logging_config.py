"""Centralized Loguru configuration for TEL3SIS."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger


def configure_logging() -> None:
    """Configure Loguru based on environment variables."""
    level = os.getenv("LOG_LEVEL", "INFO")
    rotation = os.getenv("LOG_ROTATION", "10 MB")
    log_file = os.getenv("LOG_FILE", "logs/tel3sis.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, level=level)
    logger.add(log_file, rotation=rotation, level=level, enqueue=True)


configure_logging()

__all__ = ["logger", "configure_logging"]
