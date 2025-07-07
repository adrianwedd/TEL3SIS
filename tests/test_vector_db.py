from __future__ import annotations

from server.vector_db import VectorDB


def test_add_and_search(tmp_path):
    db = VectorDB(persist_directory=str(tmp_path))
    db.add_texts(["hello world", "goodbye"])
    results = db.search("hello world", n_results=1)
    assert results[0] == "hello world"
