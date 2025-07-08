"""Utilities for language detection."""

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


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
