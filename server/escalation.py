from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

"""Utilities for escalation keyword detection."""

if TYPE_CHECKING:  # pragma: no cover - for typing only
    from .state_manager import StateManager

ESCALATION_KEYWORDS: set[str] = {
    "help",
    "human",
    "representative",
    "operator",
    "emergency",
}


def contains_keyword(text: str, keywords: Iterable[str] = ESCALATION_KEYWORDS) -> bool:
    """Return ``True`` if the text contains any escalation keyword."""
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


def check_and_flag(state_manager: "StateManager", call_sid: str, text: str) -> bool:
    """Update session state if escalation is requested."""
    if contains_keyword(text, ESCALATION_KEYWORDS):
        state_manager.update_session(call_sid, escalation_required="true")
        return True
    return False
