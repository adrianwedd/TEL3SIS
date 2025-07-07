from __future__ import annotations

import asyncio

from loguru import logger
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.streaming.synthesizer.default_factory import DefaultSynthesizerFactory
from vocode.streaming.transcriber.whisper_cpp_transcriber import WhisperCPPTranscriber
from vocode.streaming.streaming_conversation import StreamingConversation

from agents.core_agent import FunctionCallingAgent, build_core_agent


async def main() -> None:
    """Start a local StreamingConversation using the default audio devices."""
    mic, speaker = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True
    )

    config = build_core_agent()
    agent = FunctionCallingAgent(config.agent)
    transcriber = WhisperCPPTranscriber(config.transcriber)
    synthesizer = DefaultSynthesizerFactory().create_synthesizer(config.synthesizer)

    conversation = StreamingConversation(
        output_device=speaker,
        transcriber=transcriber,
        agent=agent,
        synthesizer=synthesizer,
    )

    conversation.warmup_synthesizer()
    await conversation.start()

    logger.info("Conversation started. Press Ctrl+C to stop.")

    try:
        while conversation.is_active():
            chunk = await mic.get_audio()
            conversation.receive_audio(chunk)
    except KeyboardInterrupt:
        logger.info("Stopping conversation...")
    finally:
        await conversation.terminate()
        speaker.terminate()


if __name__ == "__main__":
    asyncio.run(main())
