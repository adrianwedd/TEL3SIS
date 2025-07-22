"""Utilities for language detection."""

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

# Very small mapping of phone number country codes to preferred language.
# The mapping only covers a few common cases and defaults to English.
_NUMBER_LANG_MAP = {
    "+34": "es",  # Spain
    "+52": "es",  # Mexico
    "+33": "fr",  # France
    "+49": "de",  # Germany
    "+55": "pt",  # Brazil
    "+81": "ja",  # Japan
    "+86": "zh",  # China
    "+91": "hi",  # India
    "+44": "en",  # UK
    "+1": "en",  # US/Canada
}

# Mapping of languages to default STT and TTS engine names.
_ENGINE_MAP: dict[str, tuple[str, str]] = {
    "en": ("whisper_cpp", "elevenlabs"),
    "es": ("whisper_cpp", "elevenlabs"),
    "fr": ("whisper_cpp", "elevenlabs"),
    "de": ("whisper_cpp", "elevenlabs"),
    "pt": ("whisper_cpp", "elevenlabs"),
    "ja": ("whisper_cpp", "elevenlabs"),
    "zh": ("whisper_cpp", "elevenlabs"),
    "hi": ("whisper_cpp", "elevenlabs"),
}


def detect_language(text: str, default: str = "en") -> str:
    """Return ISO language code detected in ``text``.

    Parameters
    ----------
    text: str
        Text to analyze.
    default: str, optional
        Value to return if detection fails. Defaults to ``"en"``.
    """

    try:
        return detect(text)
    except LangDetectException:  # pragma: no cover - rare
        return default


def guess_language_from_number(phone_number: str, default: str = "en") -> str:
    """Return language code inferred from ``phone_number`` prefix.

    The logic is intentionally simple and relies on a small lookup table.
    """

    for prefix, lang in _NUMBER_LANG_MAP.items():
        if phone_number.startswith(prefix):
            return lang
    return default


def get_engines_for_language(lang: str) -> tuple[str, str]:
    """Return (STT, TTS) engine names for ``lang``."""

    return _ENGINE_MAP.get(lang, ("whisper_cpp", "elevenlabs"))
