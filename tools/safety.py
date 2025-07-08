from __future__ import annotations

import os
import re
from typing import Any

from loguru import logger

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
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return _heuristic_check(text)
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to init OpenAI client: %s", exc)
            return _heuristic_check(text)

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_SAFETY_MODEL", "gpt-3.5-turbo"),
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
        )
        verdict = resp["choices"][0]["message"]["content"].strip().upper()
        return verdict == "SAFE"
    except Exception as exc:  # noqa: BLE001
        logger.error("Safety check failed: %s", exc)
        return _heuristic_check(text)
