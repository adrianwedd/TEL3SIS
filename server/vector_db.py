from __future__ import annotations

import hashlib
import os
from typing import Iterable, List, Sequence, Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings


class SimpleEmbeddingFunction(EmbeddingFunction):
    """Deterministic embedding function based on SHA256 hash."""

    def __init__(self, dim: int = 128) -> None:
        self.dim = dim

    def __call__(self, texts: Sequence[str]) -> Embeddings:
        embeddings: List[List[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            data = list(digest) * ((self.dim + len(digest) - 1) // len(digest))
            embeddings.append([b / 255 for b in data[: self.dim]])
        return embeddings


class VectorDB:
    """Wrapper around ChromaDB for semantic memory."""

    def __init__(
        self,
        persist_directory: str | None = None,
        *,
        collection_name: str = "memory",
        embedding_function: Optional[EmbeddingFunction] = None,
    ) -> None:
        persist_directory = persist_directory or os.getenv(
            "VECTOR_DB_PATH", "vector_store"
        )
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function or SimpleEmbeddingFunction(),
        )

    def add_texts(
        self, texts: Iterable[str], ids: Optional[Iterable[str]] = None
    ) -> None:
        docs = list(texts)
        if not docs:
            return
        id_list = list(ids) if ids is not None else [str(hash(doc)) for doc in docs]
        self.collection.add(documents=docs, ids=id_list)

    def search(self, query: str, n_results: int = 3) -> List[str]:
        result = self.collection.query(query_texts=[query], n_results=n_results)
        return result.get("documents", [[]])[0]
