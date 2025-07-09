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
