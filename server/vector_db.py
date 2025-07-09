from __future__ import annotations

import os
import hashlib
from typing import Iterable, List, Sequence, Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer


class STEmbeddingFunction(EmbeddingFunction):
    """Embedding function backed by SentenceTransformers."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        name = model_name or os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        try:
            self.model = SentenceTransformer(name)
            self._fallback = False
        except Exception:
            # Offline fallback using deterministic hash embeddings
            self._fallback = True
            self._dim = 128

    def __call__(self, texts: Sequence[str]) -> Embeddings:
        if self._fallback:
            embeddings: List[List[float]] = []
            for text in texts:
                digest = hashlib.sha256(text.encode()).digest()
                data = list(digest) * ((self._dim + len(digest) - 1) // len(digest))
                embeddings.append([b / 255 for b in data[: self._dim]])
            return embeddings
        vectors = self.model.encode(list(texts))
        return vectors.tolist()


class VectorDB:
    """Wrapper around ChromaDB for semantic memory."""

    def __init__(
        self,
        persist_directory: str | None = None,
        *,
        collection_name: str = "memory",
        embedding_function: Optional[EmbeddingFunction] = None,
        model_name: Optional[str] = None,
    ) -> None:
        persist_directory = persist_directory or os.getenv(
            "VECTOR_DB_PATH", "vector_store"
        )
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function
            or STEmbeddingFunction(model_name=model_name),
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
