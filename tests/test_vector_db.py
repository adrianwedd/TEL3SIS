from __future__ import annotations

import os

from server.vector_db import VectorDB


def test_add_and_search(tmp_path):
    os.environ.setdefault("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    db = VectorDB(persist_directory=str(tmp_path))
    db.add_texts(["hello world", "goodbye"])
    results = db.search("hello world", n_results=1)
    assert results[0] == "hello world"


def test_summary_collection(tmp_path):
    os.environ.setdefault("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    db = VectorDB(persist_directory=str(tmp_path), collection_name="summaries")
    db.add_texts(["ask about weather"], ids=["c1"])
    result = db.search("weather", n_results=1)
    assert result[0] == "ask about weather"
