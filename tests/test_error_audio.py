import sys
import types
import asyncio
from importlib import reload
from dataclasses import dataclass

# Stub heavy chromadb dependency before importing core modules
chroma = types.ModuleType("chromadb")


class _DummyCollection:
    def add(self, **_: object) -> None:  # pragma: no cover - stub
        pass

    def query(self, **_: object):  # pragma: no cover - stub
        return {"documents": [[]]}


class _DummyClient:
    def __init__(self, *_: object, **__: object) -> None:
        pass

    def get_or_create_collection(self, *_: object, **__: object):
        return _DummyCollection()

    def heartbeat(self) -> int:
        return 1


chroma.PersistentClient = lambda *a, **k: _DummyClient()
sys.modules["chromadb"] = chroma
sys.modules["chromadb.api"] = types.ModuleType("chromadb.api")
sys.modules["chromadb.api.types"] = types.SimpleNamespace(
    EmbeddingFunction=object, Embeddings=list
)

from server import vector_db as vdb  # noqa: E402


class _DummyModel:
    def encode(self, texts):
        return [[0.0, 0.0] for _ in texts]


vdb.SentenceTransformer = lambda *a, **k: _DummyModel()


def setup_dummy_vocode():
    dummy = types.ModuleType("vocode")
    dummy.streaming = types.ModuleType("vocode.streaming")
    dummy.streaming.agent = types.ModuleType("vocode.streaming.agent")
    dummy.streaming.agent.chat_gpt_agent = types.ModuleType(
        "vocode.streaming.agent.chat_gpt_agent"
    )
    dummy.streaming.agent.base_agent = types.ModuleType(
        "vocode.streaming.agent.base_agent"
    )
    dummy.streaming.agent.default_factory = types.ModuleType(
        "vocode.streaming.agent.default_factory"
    )
    dummy.streaming.models = types.ModuleType("vocode.streaming.models")
    dummy.streaming.models.agent = types.ModuleType("vocode.streaming.models.agent")
    dummy.streaming.models.actions = types.ModuleType("vocode.streaming.models.actions")
    dummy.streaming.models.message = types.ModuleType("vocode.streaming.models.message")
    dummy.streaming.models.transcriber = types.ModuleType(
        "vocode.streaming.models.transcriber"
    )
    dummy.streaming.models.synthesizer = types.ModuleType(
        "vocode.streaming.models.synthesizer"
    )

    class Dummy:
        def __init__(self, *args, **kwargs):
            pass

    @dataclass
    class DummyEvent:
        message: object
        is_interruptible: bool = False

    @dataclass
    class DummyMessage:
        text: str | None = None

    dummy.streaming.agent.chat_gpt_agent.ChatGPTAgent = Dummy
    dummy.streaming.agent.base_agent.AgentInput = Dummy
    dummy.streaming.agent.base_agent.AgentResponseMessage = DummyEvent
    dummy.streaming.agent.base_agent.BaseAgent = Dummy
    dummy.streaming.agent.base_agent.GeneratedResponse = DummyEvent
    dummy.streaming.agent.default_factory.DefaultAgentFactory = Dummy
    dummy.streaming.models.agent.AgentConfig = Dummy
    dummy.streaming.models.agent.ChatGPTAgentConfig = Dummy
    dummy.streaming.models.actions.FunctionCall = Dummy
    dummy.streaming.models.message.BaseMessage = DummyMessage
    dummy.streaming.models.message.EndOfTurn = Dummy
    dummy.streaming.models.transcriber.WhisperCPPTranscriberConfig = Dummy
    dummy.streaming.models.synthesizer.ElevenLabsSynthesizerConfig = Dummy

    modules = {
        "vocode": dummy,
        "vocode.streaming": dummy.streaming,
        "vocode.streaming.agent": dummy.streaming.agent,
        "vocode.streaming.agent.chat_gpt_agent": dummy.streaming.agent.chat_gpt_agent,
        "vocode.streaming.agent.base_agent": dummy.streaming.agent.base_agent,
        "vocode.streaming.agent.default_factory": dummy.streaming.agent.default_factory,
        "vocode.streaming.models": dummy.streaming.models,
        "vocode.streaming.models.agent": dummy.streaming.models.agent,
        "vocode.streaming.models.actions": dummy.streaming.models.actions,
        "vocode.streaming.models.message": dummy.streaming.models.message,
        "vocode.streaming.models.transcriber": dummy.streaming.models.transcriber,
        "vocode.streaming.models.synthesizer": dummy.streaming.models.synthesizer,
    }
    sys.modules.update(modules)
    return modules


def test_tool_error(monkeypatch):
    setup_dummy_vocode()
    import agents.core_agent as cg

    reload(cg)

    msgs = []

    class DummyAgent(cg.FunctionCallingAgent):
        def produce_interruptible_agent_response_event_nonblocking(
            self, event, is_interruptible=False
        ):
            if hasattr(event.message, "text"):
                msgs.append(event.message.text)

    agent = DummyAgent(cg.FunctionChatGPTAgentConfig(functions=[]))

    async def boom(*_, **__):
        raise RuntimeError("fail")

    monkeypatch.setattr(agent, "handle_function_call", boom)
    func = types.SimpleNamespace(name="get_weather", arguments="{}")
    asyncio.run(agent.call_function(func, types.SimpleNamespace()))
    assert msgs and msgs[-1].startswith("I am having trouble")


def test_llm_error(monkeypatch):
    setup_dummy_vocode()
    import agents.core_agent as cg

    reload(cg)

    msgs = []

    class ErrorChatGPT:
        async def generate_response(self, *_, **__):
            raise RuntimeError("nope")

    monkeypatch.setattr(cg, "ChatGPTAgent", ErrorChatGPT)
    agent = cg.SafeFunctionCallingAgent(cg.FunctionChatGPTAgentConfig(functions=[]))

    async def run():
        async for resp in agent.generate_response("hi", "c"):
            if hasattr(resp.message, "text"):
                msgs.append(resp.message.text)

    asyncio.run(run())
    assert any(m.startswith("I am experiencing") for m in msgs)
