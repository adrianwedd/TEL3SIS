from __future__ import annotations

import os
from dataclasses import dataclass

from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.transcriber import WhisperCPPTranscriberConfig
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig


@dataclass
class CoreAgentConfig:
    """Container for the main agent and voice settings."""

    agent: ChatGPTAgentConfig
    transcriber: WhisperCPPTranscriberConfig
    synthesizer: ElevenLabsSynthesizerConfig


def build_core_agent() -> CoreAgentConfig:
    """Return TEL3SIS ChatGPT agent with STT and TTS providers configured."""

    agent_config = ChatGPTAgentConfig(
        prompt_preamble="You are TEL3SIS, a helpful voice assistant.",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )

    transcriber_config = WhisperCPPTranscriberConfig.from_telephone_input_device()
    synthesizer_config = ElevenLabsSynthesizerConfig.from_telephone_output_device(
        api_key=os.getenv("ELEVEN_LABS_API_KEY")
    )

    return CoreAgentConfig(
        agent=agent_config,
        transcriber=transcriber_config,
        synthesizer=synthesizer_config,
    )
