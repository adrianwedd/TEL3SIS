from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from .tasks import summarize_text

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
        summarize_conversation(state_manager, call_sid)
        return True
    return False


def summarize_conversation(
    state_manager: "StateManager", call_sid: str, max_words: int = 50
) -> str:
    """Generate and persist a summary of the call history."""
    history = state_manager.get_history(call_sid)
    text = " ".join(entry.get("text", "") for entry in history)
    # ``summarize_text`` is a Celery task; ``.run`` executes the underlying
    # function synchronously.
    try:
        summary = summarize_text.run(text, max_words=max_words)
    except AttributeError:  # pragma: no cover - fallback if not a task
        summary = summarize_text(text, max_words=max_words)
    session = state_manager.get_session(call_sid)
    from_number = session.get("from")
    state_manager.set_summary(call_sid, summary, from_number=from_number)
    return summary
