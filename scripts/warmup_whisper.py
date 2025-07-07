from __future__ import annotations

import time

from loguru import logger
import whisper


MODEL: whisper.Whisper | None = None


def load_model(model_name: str = "base") -> whisper.Whisper:
    """Load and return a Whisper model, caching globally."""
    global MODEL
    if MODEL is None:
        start = time.perf_counter()
        logger.info("Loading Whisper model '%s'...", model_name)
        MODEL = whisper.load_model(model_name)
        elapsed = time.perf_counter() - start
        logger.info("Whisper model loaded in %.2f seconds", elapsed)
    return MODEL


if __name__ == "__main__":
    load_model()
