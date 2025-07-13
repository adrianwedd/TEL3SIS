"""Simple dialogue state machine for multi-turn event scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class DialogueStateMachine:
    """Track conversation context across turns."""

    state: str = "ask_title"
    data: Dict[str, str] = field(default_factory=dict)

    def next_prompt(self) -> str:
        if self.state == "ask_title":
            return "What is the event title?"
        if self.state == "ask_date":
            return "What date is the event?"
        if self.state == "ask_time":
            return "What time does it start?"
        if self.state == "confirm":
            title = self.data.get("title", "")
            date = self.data.get("date", "")
            time = self.data.get("time", "")
            return f"You want to schedule '{title}' on {date} at {time}, correct?"
        return "Thank you."

    def handle_input(self, text: str) -> str:
        """Update state based on user input and return the next prompt."""
        if self.state == "ask_title":
            self.data["title"] = text
            self.state = "ask_date"
        elif self.state == "ask_date":
            self.data["date"] = text
            self.state = "ask_time"
        elif self.state == "ask_time":
            self.data["time"] = text
            self.state = "confirm"
        elif self.state == "confirm":
            if text.strip().lower() in {"yes", "y", "correct"}:
                self.state = "done"
            else:
                # restart to gather details again
                self.state = "ask_title"
                self.data.clear()
        return self.next_prompt()

    def is_complete(self) -> bool:
        return self.state == "done"

    def get_event_details(self) -> Dict[str, str]:
        return dict(self.data)
