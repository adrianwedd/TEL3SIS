from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from loguru import logger
import json
import asyncio

from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.agent.base_agent import AgentInput, AgentResponseMessage
from vocode.streaming.models.actions import FunctionCall
from vocode.streaming.models.message import BaseMessage, EndOfTurn

from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.transcriber import WhisperCPPTranscriberConfig
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig

from tools.weather import get_weather
from server.state_manager import StateManager
from tools.calendar import AuthError


WEATHER_FUNCTION = {
    "name": "get_weather",
    "description": "Get the current weather for a location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City or region name",
            }
        },
        "required": ["location"],
    },
}


@dataclass
class FunctionChatGPTAgentConfig(ChatGPTAgentConfig):
    """ChatGPT config that exposes OpenAI function schemas."""

    functions: List[Dict[str, Any]] | None = field(default_factory=list)


@dataclass
class CoreAgentConfig:
    """Container for the main agent and voice settings."""

    agent: FunctionChatGPTAgentConfig
    transcriber: WhisperCPPTranscriberConfig
    synthesizer: ElevenLabsSynthesizerConfig


class FunctionCallingAgent(ChatGPTAgent):
    """Agent subclass that dispatches OpenAI function calls."""

    def __init__(
        self,
        agent_config: FunctionChatGPTAgentConfig,
        function_map: Optional[Dict[str, Callable[..., Any]]] = None,
        state_manager: Optional[StateManager] = None,
        call_sid: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(agent_config, **kwargs)
        self.function_map = {"get_weather": get_weather}
        if function_map:
            self.function_map.update(function_map)
        self.state_manager = state_manager
        self.call_sid = call_sid

    def get_functions(self) -> List[Dict[str, Any]] | None:  # type: ignore[override]
        return self.agent_config.functions

    async def handle_function_call(self, function_call: FunctionCall) -> Optional[str]:
        """Execute the mapped Python function and return its string result."""
        func = self.function_map.get(function_call.name)
        if func is None:
            logger.error("Unknown function: %s", function_call.name)
            return None
        try:
            params = json.loads(function_call.arguments or "{}")
            if self.state_manager and self.call_sid:
                session = self.state_manager.get_session(self.call_sid)
                user_phone = session.get("from")
                twilio_phone = session.get("to")
                if user_phone and twilio_phone:
                    params.setdefault("user_phone", user_phone)
                    params.setdefault("twilio_phone", twilio_phone)
        except json.JSONDecodeError as exc:
            logger.error("Invalid arguments for %s: %s", function_call.name, exc)
            return None
        result = func(**params)
        if asyncio.iscoroutine(result):
            result = await result
        return str(result) if result is not None else None

    async def call_function(self, function_call: FunctionCall, agent_input: AgentInput) -> None:  # type: ignore[override]
        try:
            response_text = await self.handle_function_call(function_call)
        except AuthError:
            fallback = "I need your permission to do that. I'll text you a link."
            self.produce_interruptible_agent_response_event_nonblocking(
                AgentResponseMessage(message=BaseMessage(text=fallback)),
                is_interruptible=True,
            )
            self.produce_interruptible_agent_response_event_nonblocking(
                AgentResponseMessage(message=EndOfTurn())
            )
            return
        if not response_text:
            return
        self.produce_interruptible_agent_response_event_nonblocking(
            AgentResponseMessage(message=BaseMessage(text=response_text)),
            is_interruptible=True,
        )
        self.produce_interruptible_agent_response_event_nonblocking(
            AgentResponseMessage(message=EndOfTurn())
        )


def build_core_agent(
    state_manager: StateManager, call_sid: str | None = None
) -> CoreAgentConfig:
    """Return TEL3SIS ChatGPT agent with STT and TTS providers configured."""

    agent_config = FunctionChatGPTAgentConfig(
        prompt_preamble="You are TEL3SIS, a helpful voice assistant.",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        functions=[WEATHER_FUNCTION],
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
