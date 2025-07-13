from __future__ import annotations

import re
from typing import Any

from server.config import Config

from loguru import logger
from util import call_with_retries

__all__ = ["safety_check"]


_BANNED_PATTERNS = [r"\bkill\b", r"\bbomb\b", r"\battack\b", r"\bterror\b"]


def _heuristic_check(text: str) -> bool:
    """Return True if text appears safe based on regex patterns."""
    for pattern in _BANNED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True


def safety_check(text: str, *, client: Any | None = None) -> bool:
    """Return ``True`` if the proposed response passes the safety check."""

    if client is None:
        api_key = Config().openai_api_key
        if not api_key:
            return _heuristic_check(text)
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to init OpenAI client: %s", exc)
            return _heuristic_check(text)

    try:
        resp = call_with_retries(
            client.chat.completions.create,
            model=Config().openai_safety_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Respond with SAFE if the text is policy compliant. "
                        "Respond with UNSAFE otherwise."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=1,
            temperature=0,
            timeout=10,
        )
        verdict = resp["choices"][0]["message"]["content"].strip().upper()
        return verdict == "SAFE"
    except Exception as exc:  # noqa: BLE001
        logger.error("Safety check failed: %s", exc)
        return _heuristic_check(text)
