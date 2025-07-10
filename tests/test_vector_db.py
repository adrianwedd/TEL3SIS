from __future__ import annotations

import pytest

from server import vector_db as vdb


class DummyModel:
    def __init__(self, name: str) -> None:
        self.name = name

    def encode(self, texts: list[str]):
        import numpy as np

        return np.zeros((len(texts), 2))


def test_add_and_search(tmp_path, monkeypatch):
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "dummy-model")
    monkeypatch.setattr(vdb, "SentenceTransformer", DummyModel)
    db = vdb.VectorDB(persist_directory=str(tmp_path))
    db.add_texts(["hello world", "goodbye"])
    results = db.search("hello world", n_results=1)
    assert results[0] in {"hello world", "goodbye"}


def test_summary_collection(tmp_path, monkeypatch):
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "dummy-model")
    monkeypatch.setattr(vdb, "SentenceTransformer", DummyModel)
    db = vdb.VectorDB(persist_directory=str(tmp_path), collection_name="summaries")
    db.add_texts(["ask about weather"], ids=["c1"])
    result = db.search("weather", n_results=1)
    assert result[0] == "ask about weather"


def test_embedding_function_model_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL_NAME", "dummy-model")
    monkeypatch.setattr(vdb, "SentenceTransformer", DummyModel)
    func = vdb.STEmbeddingFunction()
    assert isinstance(func.model, DummyModel)
    assert func.model.name == "dummy-model"


class DummyEmbeddingResp:
    def __init__(self, n: int) -> None:
        self.data = [type("Obj", (), {"embedding": [0.0, 0.0]})() for _ in range(n)]


class DummyOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = type(
            "Embeddings",
            (),
            {"create": lambda self, input, model: DummyEmbeddingResp(len(input))},
        )()


class DummyOpenAIEmbedding:
    def __call__(self, input: list[str]):  # noqa: ANN001
        return [[0.0, 0.0] for _ in input]


def test_openai_embedding_function(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    func = vdb.OpenAIEmbeddingFunction(model_name="foo", api_key="sk-test")
    monkeypatch.setattr(func, "client", DummyOpenAIClient())
    vecs = func(["a", "b"])
    assert len(vecs) == 2


def test_vector_db_openai_provider(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(
        vdb, "OpenAIEmbeddingFunction", lambda model_name=None: DummyOpenAIEmbedding()
    )
    db = vdb.VectorDB(persist_directory=str(tmp_path))
    db.add_texts(["x"])
    assert db.search("x")[0] == "x"
