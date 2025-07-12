import base64
import types
import sys
from pathlib import Path

import fakeredis
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

chroma = types.ModuleType("chromadb")


class _DummyCollection:
    def add(self, **_: object) -> None:
        pass

    def query(self, **_: object):
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


class DummySynthesizer:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class DummyTranscriber:
    def __init__(self) -> None:
        self.restarted = False

    def restart(self) -> None:
        self.restarted = True


def _make_manager(monkeypatch):
    from server.state_manager import StateManager

    key = AESGCM.generate_key(bit_length=128)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(key).decode())
    monkeypatch.setenv("VECTOR_DB_PATH", str(Path("vectors")))
    manager = StateManager(url="redis://localhost:6379/0")
    manager._redis = fakeredis.FakeRedis(decode_responses=True)
    return manager


def test_barge_in_detection(monkeypatch) -> None:
    from tel3sis.barge_in import BargeInController

    manager = _make_manager(monkeypatch)
    manager.create_session("c1", {"init": "1"})
    synth = DummySynthesizer()
    trans = DummyTranscriber()
    ctrl = BargeInController(synth, trans, manager, "c1")

    ctrl.start_speech()
    interrupted = ctrl.process_audio(b"hello")

    assert interrupted is True
    assert synth.stopped is True
    assert trans.restarted is True
    assert manager.get_session("c1")["state"] == "listening"


def test_no_barge_on_silence(monkeypatch) -> None:
    from tel3sis.barge_in import BargeInController

    manager = _make_manager(monkeypatch)
    manager.create_session("c2", {"init": "1"})
    synth = DummySynthesizer()
    trans = DummyTranscriber()
    ctrl = BargeInController(synth, trans, manager, "c2")

    ctrl.start_speech()
    interrupted = ctrl.process_audio(b"\x00\x00")

    assert interrupted is False
    assert synth.stopped is False
    assert trans.restarted is False
    assert manager.get_session("c2")["state"] == "speaking"
