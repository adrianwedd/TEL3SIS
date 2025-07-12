"""Centralized Loguru configuration for TEL3SIS."""

from __future__ import annotations

import sys
from pathlib import Path

from server.config import Config

from loguru import logger


def configure_logging() -> None:
    """Configure Loguru based on environment variables."""
    cfg = Config()
    level = cfg.log_level
    rotation = cfg.log_rotation
    log_file = cfg.log_file
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, level=level)
    logger.add(log_file, rotation=rotation, level=level, enqueue=True)


configure_logging()

__all__ = ["logger", "configure_logging"]
