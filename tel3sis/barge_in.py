from __future__ import annotations

from typing import Any

from server.state_manager import StateManager


class BargeInController:
    """Detect user interruptions and manage STT/TTS switching."""

    def __init__(
        self,
        synthesizer: Any,
        transcriber: Any,
        state_manager: StateManager,
        call_sid: str,
    ) -> None:
        self.synthesizer = synthesizer
        self.transcriber = transcriber
        self.state_manager = state_manager
        self.call_sid = call_sid
        self._speaking = False

    def start_speech(self) -> None:
        """Mark that the bot started speaking."""
        self._speaking = True
        self.state_manager.update_session(self.call_sid, state="speaking")

    def end_speech(self) -> None:
        """Mark that the bot finished speaking."""
        self._speaking = False
        self.state_manager.update_session(self.call_sid, state="listening")

    def process_audio(self, chunk: bytes) -> bool:
        """Handle an incoming audio chunk.

        Returns ``True`` if playback was interrupted.
        """
        if not self._speaking:
            return False
        if not chunk or all(b == 0 for b in chunk):
            return False

        if hasattr(self.synthesizer, "stop"):
            try:
                self.synthesizer.stop()
            except Exception:  # pragma: no cover - defensive
                pass

        if hasattr(self.transcriber, "restart"):
            try:
                self.transcriber.restart()
            except Exception:  # pragma: no cover - defensive
                pass

        self._speaking = False
        self.state_manager.update_session(self.call_sid, state="listening")
        return True
