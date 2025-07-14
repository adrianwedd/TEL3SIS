from __future__ import annotations

import time

from logging_config import logger
import whisper


MODEL: whisper.Whisper | None = None


def load_model(model_name: str = "base") -> whisper.Whisper:
    """Load and return a Whisper model, caching globally."""
    global MODEL
    if MODEL is None:
        start = time.perf_counter()
        logger.bind(model=model_name).info("load_whisper_start")
        MODEL = whisper.load_model(model_name)
        elapsed = time.perf_counter() - start
        logger.bind(model=model_name, duration=elapsed).info("load_whisper_complete")
    return MODEL


if __name__ == "__main__":
    load_model()
