"""Utilities for translating text between languages."""
from __future__ import annotations

from deep_translator import GoogleTranslator
from logging_config import logger
from server.cache import redis_cache
from .base import Tool

__all__ = ["translate_text", "TranslateTool"]


@redis_cache(ttl=3600)
def translate_text(text: str, target_lang: str, source_lang: str | None = None) -> str:
    """Return ``text`` translated into ``target_lang``."""
    try:
        translator = GoogleTranslator(source=source_lang or "auto", target=target_lang)
        return translator.translate(text)
    except Exception as exc:  # noqa: BLE001
        logger.bind(target_lang=target_lang, error=str(exc)).error("translate_failed")
        return "Sorry, I'm unable to translate that right now."


class TranslateTool(Tool):
    """Tool wrapper around :func:`translate_text`."""

    name = "translate"
    description = "Translate text to a target language using Google Translate."
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "target_lang": {"type": "string", "description": "Target language code"},
            "source_lang": {
                "type": "string",
                "description": "Source language code (optional)",
                "nullable": True,
            },
        },
        "required": ["text", "target_lang"],
    }

    def run(
        self, text: str, target_lang: str, source_lang: str | None = None
    ) -> str:  # type: ignore[override]
        return translate_text(text, target_lang, source_lang)
