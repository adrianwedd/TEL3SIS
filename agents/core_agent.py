from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, AsyncGenerator

from logging_config import logger
import json
import asyncio

from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.agent.base_agent import (
    AgentInput,
    AgentResponseMessage,
    GeneratedResponse,
)
from vocode.streaming.agent.default_factory import DefaultAgentFactory
from vocode.streaming.agent.base_agent import BaseAgent
from vocode.streaming.models.agent import AgentConfig
from vocode.streaming.models.actions import FunctionCall
from vocode.streaming.models.message import BaseMessage, EndOfTurn

from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.transcriber import WhisperCPPTranscriberConfig
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig
from server.settings import Settings
from server.database import get_agent_config
from tools import registry
from tools.safety import safety_check
from server.state_manager import StateManager
from tools.language import get_engines_for_language
from tools.calendar import AuthError
from requests.exceptions import RequestException
from googleapiclient.errors import HttpError
from google.auth.exceptions import GoogleAuthError
from server.metrics import external_api_calls, external_api_latency
import time


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
        if agent_config.functions is not None:
            agent_config.functions.extend(registry.schemas())
        else:
            agent_config.functions = registry.schemas()
        self.function_map = {name: tool.run for name, tool in registry.tools.items()}
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
            logger.bind(function=function_call.name).error("unknown_function")
            external_api_calls.labels(function_call.name, "unknown_function").inc()
            return None
        
        start_time = time.time()
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
            logger.bind(function=function_call.name, error=str(exc)).error(
                "invalid_arguments"
            )
            external_api_calls.labels(function_call.name, "invalid_args").inc()
            return None
        
        try:
            result = func(**params)
            if asyncio.iscoroutine(result):
                result = await result
            
            # Record successful tool call
            duration = time.time() - start_time
            external_api_calls.labels(function_call.name, "success").inc()
            external_api_latency.labels(function_call.name).observe(duration)
            
            return str(result) if result is not None else None
        except (
            RuntimeError,
            ValueError,
            HttpError,
            RequestException,
            AttributeError,
        ) as exc:
            duration = time.time() - start_time
            external_api_calls.labels(function_call.name, "error").inc()
            external_api_latency.labels(function_call.name).observe(duration)
            logger.bind(function=function_call.name, error=str(exc)).error(
                "tool_call_failed"
            )
            raise

    async def call_function(self, function_call: FunctionCall, agent_input: AgentInput) -> None:  # type: ignore[override]
        try:
            response_text = await self.handle_function_call(function_call)
        except AuthError:
            fallback = "I need your permission to do that. I'll text you a link."
            self._send_agent_response(fallback)
            return
        except (
            RuntimeError,
            ValueError,
            HttpError,
            RequestException,
            GoogleAuthError,
            AttributeError,
        ):
            # Provide more specific error messages based on exception type
            error_msg = self._get_contextual_error_message(function_call.name)
            self._send_agent_response(error_msg)
            return
        
        if not response_text:
            return
        
        self._send_agent_response(response_text)
    
    def _get_contextual_error_message(self, function_name: str) -> str:
        """Return contextual error message based on function type."""
        error_messages = {
            "get_weather": "I'm having trouble getting weather information right now. Please try again in a moment.",
            "create_calendar_event": "I can't access your calendar at the moment. Please try scheduling the event later.",
            "send_sms": "I'm unable to send text messages right now. Please try again shortly.",
            "send_email": "I'm having trouble sending emails at the moment. Please try again later.",
        }
        return error_messages.get(
            function_name, 
            "I am having trouble reaching that service right now. Please try again later."
        )
    
    def _send_agent_response(self, text: str) -> None:
        """Helper to send agent response with consistent formatting."""
        self.produce_interruptible_agent_response_event_nonblocking(
            AgentResponseMessage(message=BaseMessage(text=text)),
            is_interruptible=True,
        )
        self.produce_interruptible_agent_response_event_nonblocking(
            AgentResponseMessage(message=EndOfTurn())
        )


class SafeFunctionCallingAgent(FunctionCallingAgent):
    """FunctionCallingAgent with a safety filter on LLM output."""

    async def generate_response(
        self,
        human_input: str,
        conversation_id: str,
        is_interrupt: bool = False,
        bot_was_in_medias_res: bool = False,
    ) -> AsyncGenerator[GeneratedResponse, None]:
        parts: List[str] = []
        responses: List[GeneratedResponse] = []
        try:
            async for resp in super().generate_response(
                human_input,
                conversation_id,
                is_interrupt=is_interrupt,
                bot_was_in_medias_res=bot_was_in_medias_res,
            ):
                if hasattr(resp.message, "text"):
                    parts.append(getattr(resp.message, "text"))
                responses.append(resp)
        except (
            RuntimeError,
            HttpError,
            RequestException,
            GoogleAuthError,
            AttributeError,
        ) as exc:
            logger.bind(error=str(exc)).error("llm_error")
            yield GeneratedResponse(
                message=BaseMessage(
                    text="I am experiencing technical difficulties. Let us continue another time."
                ),
                is_interruptible=True,
            )
            yield GeneratedResponse(message=EndOfTurn(), is_interruptible=True)
            return

        full_text = "".join(parts)
        if not safety_check(full_text):
            yield GeneratedResponse(
                message=BaseMessage(text="I'm sorry, I can't help with that."),
                is_interruptible=True,
            )
            yield GeneratedResponse(message=EndOfTurn(), is_interruptible=True)
        else:
            for resp in responses:
                yield resp


class SafeAgentFactory(DefaultAgentFactory):
    """AgentFactory that returns ``SafeFunctionCallingAgent`` for ChatGPT configs."""

    def create_agent(self, agent_config: AgentConfig) -> BaseAgent:  # type: ignore[override]
        if isinstance(agent_config, ChatGPTAgentConfig):
            return SafeFunctionCallingAgent(agent_config)
        return super().create_agent(agent_config)


def build_core_agent(
    state_manager: StateManager, call_sid: str | None = None, language: str = "en"
) -> CoreAgentConfig:
    """Return TEL3SIS ChatGPT agent with STT and TTS providers configured."""

    cfg = Settings()
    stored = get_agent_config()
    agent_config = FunctionChatGPTAgentConfig(
        prompt_preamble=stored.get(
            "prompt", "You are TEL3SIS, a helpful voice assistant."
        ),
        openai_api_key=cfg.openai_api_key,
        functions=registry.schemas(),
    )

    stt_engine, tts_engine = get_engines_for_language(language)

    if stt_engine == "whisper_cpp":
        transcriber_config = WhisperCPPTranscriberConfig.from_telephone_input_device()
    else:  # pragma: no cover - fallback until other engines are supported
        transcriber_config = WhisperCPPTranscriberConfig.from_telephone_input_device()
    setattr(transcriber_config, "language", language)

    if tts_engine == "elevenlabs":
        synthesizer_config = ElevenLabsSynthesizerConfig.from_telephone_output_device(
            api_key=cfg.eleven_labs_api_key
        )
    else:  # pragma: no cover - fallback until other engines are supported
        synthesizer_config = ElevenLabsSynthesizerConfig.from_telephone_output_device(
            api_key=cfg.eleven_labs_api_key
        )
    setattr(synthesizer_config, "language", language)
    voice = stored.get("voice")
    if voice:
        setattr(synthesizer_config, "voice", voice)

    return CoreAgentConfig(
        agent=agent_config,
        transcriber=transcriber_config,
        synthesizer=synthesizer_config,
    )


def get_core_agent(
    state_manager: StateManager, call_sid: str | None = None, language: str = "en"
) -> AgentConfig:
    """Return just the Vocode ``AgentConfig`` for the core agent."""

    return build_core_agent(state_manager, call_sid, language).agent
